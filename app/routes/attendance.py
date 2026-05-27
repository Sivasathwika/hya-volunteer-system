"""Attendance routes - QR check-in/check-out endpoints."""

from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app.models.event import Event
from app.services.attendance_service import AttendanceService
from app.utils.decorators import admin_only
import logging

logger = logging.getLogger(__name__)

attendance_bp = Blueprint('attendance', __name__, url_prefix='/attendance')


@attendance_bp.route('/events/<int:event_id>/qr-scanner')
@login_required
@admin_only
def qr_scanner(event_id):
    """QR scanner interface for checking in volunteers."""
    event = Event.query.get_or_404(event_id)
    stats = AttendanceService.get_event_attendance_stats(event_id)
    return render_template('attendance/qr_scanner.html', event=event, stats=stats if stats.get('success') else {})


@attendance_bp.route('/check-in', methods=['POST'])
@login_required
@admin_only
def check_in():
    """API endpoint for check-in via QR code."""
    data = request.get_json()
    qr_code = data.get('qr_code', '').strip()
    
    if not qr_code:
        return jsonify({'success': False, 'message': 'No QR code'}), 400
    
    result = AttendanceService.check_in_volunteer(qr_code)
    return jsonify(result), (200 if result['success'] else 400)


@attendance_bp.route('/check-out', methods=['POST'])
@login_required
@admin_only
def check_out():
    """API endpoint for check-out via QR code."""
    data = request.get_json()
    qr_code = data.get('qr_code', '').strip()
    
    if not qr_code:
        return jsonify({'success': False, 'message': 'No QR code'}), 400
    
    result = AttendanceService.check_out_volunteer(qr_code)
    return jsonify(result), (200 if result['success'] else 400)


@attendance_bp.route('/events/<int:event_id>/stats')
@login_required
@admin_only
def event_attendance_stats(event_id):
    """Get real-time attendance statistics."""
    stats = AttendanceService.get_event_attendance_stats(event_id)
    return jsonify(stats)


@attendance_bp.route('/events/<int:event_id>/history')
@login_required
@admin_only
def event_attendance_history(event_id):
    """View complete attendance history."""
    from app.models.attendance import Attendance
    event = Event.query.get_or_404(event_id)
    attendances = Attendance.query.filter_by(event_id=event_id).all()
    return render_template('attendance/history.html', event=event, attendances=attendances)