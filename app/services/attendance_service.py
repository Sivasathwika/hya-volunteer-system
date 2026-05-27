"""Attendance service - QR-based check-in and check-out logic."""

import logging
from app.database import db
from app.models.attendance import Attendance
from app.models.event import EventRegistration, Event
from datetime import datetime

logger = logging.getLogger(__name__)


class AttendanceService:
    """Attendance tracking and QR management."""
    
    @staticmethod
    def generate_qr_code_for_registration(registration: EventRegistration) -> dict:
        try:
            existing = Attendance.query.filter_by(
                volunteer_id=registration.volunteer_id,
                event_id=registration.event_id
            ).first()
            
            if existing:
                return {'success': True, 'message': 'QR code already generated', 'qr_code': existing.qr_code}
            
            qr_code = Attendance.generate_qr_code()
            attendance = Attendance(
                volunteer_id=registration.volunteer_id,
                event_id=registration.event_id,
                qr_code=qr_code,
                status=Attendance.STATUS_INCOMPLETE
            )
            
            db.session.add(attendance)
            db.session.commit()
            
            return {'success': True, 'message': 'QR code generated successfully', 'qr_code': qr_code}
        
        except Exception as e:
            db.session.rollback()
            logger.exception(f"Error generating QR code: {str(e)}")
            return {'success': False, 'message': f'Error: {str(e)}'}
    
    @staticmethod
    def check_in_volunteer(qr_code: str) -> dict:
        try:
            attendance = Attendance.query.filter_by(qr_code=qr_code).first()
            
            if not attendance:
                return {'success': False, 'message': 'Invalid QR code.'}
            
            if attendance.status == Attendance.STATUS_CHECKED_IN:
                return {'success': False, 'message': f'{attendance.volunteer.first_name} already checked in.'}
            
            if attendance.status == Attendance.STATUS_CHECKED_OUT:
                return {'success': False, 'message': f'{attendance.volunteer.first_name} already checked out.'}
            
            attendance.check_in()
            
            return {
                'success': True,
                'message': f'✓ {attendance.volunteer.first_name} checked in',
                'volunteer_name': attendance.volunteer.first_name,
                'event_name': attendance.event.title,
                'check_in_time': attendance.check_in_time.strftime('%I:%M %p')
            }
        
        except Exception as e:
            db.session.rollback()
            logger.exception(f"Error: {str(e)}")
            return {'success': False, 'message': f'Error: {str(e)}'}
    
    @staticmethod
    def check_out_volunteer(qr_code: str) -> dict:
        try:
            attendance = Attendance.query.filter_by(qr_code=qr_code).first()
            
            if not attendance:
                return {'success': False, 'message': 'Invalid QR code.'}
            
            if attendance.status == Attendance.STATUS_CHECKED_OUT:
                return {'success': False, 'message': f'{attendance.volunteer.first_name} already checked out.'}
            
            if attendance.status == Attendance.STATUS_INCOMPLETE:
                return {'success': False, 'message': f'{attendance.volunteer.first_name} never checked in.'}
            
            attendance.check_out()
            
            registration = EventRegistration.query.filter_by(
                volunteer_id=attendance.volunteer_id,
                event_id=attendance.event_id
            ).first()
            
            if registration:
                registration.mark_attended()
            
            return {
                'success': True,
                'message': f'✓ {attendance.volunteer.first_name} checked out',
                'volunteer_name': attendance.volunteer.first_name,
                'hours_served': round(attendance.hours_served, 2),
                'check_out_time': attendance.check_out_time.strftime('%I:%M %p')
            }
        
        except Exception as e:
            db.session.rollback()
            logger.exception(f"Error: {str(e)}")
            return {'success': False, 'message': f'Error: {str(e)}'}
    
    @staticmethod
    def get_event_attendance_stats(event_id: int) -> dict:
        try:
            event = Event.query.get(event_id)
            if not event:
                return {'success': False, 'message': 'Event not found'}
            
            attendances = Attendance.query.filter_by(event_id=event_id).all()
            
            checked_in = [a for a in attendances if a.status == Attendance.STATUS_CHECKED_IN]
            checked_out = [a for a in attendances if a.status == Attendance.STATUS_CHECKED_OUT]
            incomplete = [a for a in attendances if a.status == Attendance.STATUS_INCOMPLETE]
            
            total_hours = sum(a.hours_served or 0 for a in checked_out)
            
            return {
                'success': True,
                'total_registered': len(attendances),
                'checked_in_now': len(checked_in),
                'checked_out': len(checked_out),
                'incomplete': len(incomplete),
                'total_hours_served': round(total_hours, 1)
            }
        
        except Exception as e:
            logger.exception(f"Error: {str(e)}")
            return {'success': False, 'message': 'Error'}