"""
Admin routes - Dashboard, volunteer management, event creation and management.

Routes:
- GET /admin/dashboard → Admin overview and stats
- GET /admin/volunteers → List all volunteers
- GET /admin/volunteers/<id> → View volunteer details
- GET /admin/events → List all events
- POST /admin/events/create → Create new event
- GET /admin/events/<id> → Edit event
- POST /admin/events/<id>/registrations → Manage registrations (approve/reject)

Design:
- All routes require @login_required and @admin_only
- Services handle business logic
- Forms for event creation/editing
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.database import db
from app.models import User, Volunteer, Event, EventRegistration, Skill, Attendance
from app.utils.decorators import admin_only
from sqlalchemy import func
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/dashboard')
@login_required
@admin_only
def dashboard():
    """
    Admin dashboard - Overview of system statistics.
    
    Shows:
    - Total volunteers
    - Total events
    - Total volunteer hours
    - Recent registrations awaiting approval
    - Upcoming events
    """
    
    # Count statistics
    total_volunteers = Volunteer.query.count()
    total_events = Event.query.count()
    total_hours = db.session.query(func.sum(Attendance.hours_served)).scalar() or 0
    
    # Pending approvals
    pending_registrations = EventRegistration.query.filter_by(
        registration_status=EventRegistration.STATUS_PENDING
    ).count()
    
    # Upcoming events
    today = date.today()
    upcoming_events = Event.query.filter(
        Event.event_date >= today,
        Event.status != Event.STATUS_CANCELLED
    ).order_by(Event.event_date).limit(5).all()
    
    # Recent registrations
    recent_registrations = EventRegistration.query.order_by(
        EventRegistration.registered_at.desc()
    ).limit(10).all()
    
    stats = {
        'total_volunteers': total_volunteers,
        'total_events': total_events,
        'total_hours': round(total_hours, 1),
        'pending_approvals': pending_registrations
    }
    
    return render_template(
        'admin/dashboard.html',
        stats=stats,
        upcoming_events=upcoming_events,
        recent_registrations=recent_registrations
    )


@admin_bp.route('/volunteers')
@login_required
@admin_only
def volunteers():
    """
    List all volunteers with search and filtering.
    
    Shows:
    - Volunteer name, email, city
    - Total hours served
    - Events attended
    - Profile completion status
    """
    
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    query = Volunteer.query
    
    if search:
        query = query.filter(
            (Volunteer.email.ilike(f'%{search}%')) |
            (Volunteer.first_name.ilike(f'%{search}%')) |
            (Volunteer.last_name.ilike(f'%{search}%'))
        )
    
    volunteers = query.paginate(page=page, per_page=20)
    
    return render_template('admin/volunteers.html', volunteers=volunteers, search=search)


@admin_bp.route('/volunteers/<int:volunteer_id>')
@login_required
@admin_only
def volunteer_detail(volunteer_id):
    """
    View detailed information about a volunteer.
    
    Shows:
    - Profile information
    - Skills
    - Event history
    - Attendance records
    - Certificates
    """
    
    volunteer = Volunteer.query.get_or_404(volunteer_id)
    
    # Get stats
    total_hours = db.session.query(func.sum(Attendance.hours_served)).filter_by(
        volunteer_id=volunteer_id
    ).scalar() or 0
    
    events_attended = Attendance.query.filter_by(volunteer_id=volunteer_id).count()
    
    # Get recent activity
    registrations = EventRegistration.query.filter_by(
        volunteer_id=volunteer_id
    ).order_by(EventRegistration.registered_at.desc()).limit(10).all()
    
    certificates = volunteer.certificates.all()
    
    return render_template(
        'admin/volunteer_detail.html',
        volunteer=volunteer,
        total_hours=round(total_hours, 1),
        events_attended=events_attended,
        registrations=registrations,
        certificates=certificates
    )


@admin_bp.route('/events')
@login_required
@admin_only
def events():
    """
    List all events with status and statistics.
    
    Shows:
    - Event name, date, location
    - Registration count vs capacity
    - Status (draft, published, ongoing, completed, cancelled)
    """
    
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    
    query = Event.query
    
    if status and status in Event.VALID_STATUSES:
        query = query.filter_by(status=status)
    
    events = query.order_by(Event.event_date.desc()).paginate(page=page, per_page=20)
    
    return render_template(
        'admin/events.html',
        events=events,
        status_filter=status,
        valid_statuses=Event.VALID_STATUSES
    )


@admin_bp.route('/events/create', methods=['GET', 'POST'])
@login_required
@admin_only
def create_event():
    """
    Create a new event.
    
    POST data:
    - title, description
    - event_date, start_time, end_time
    - location, capacity
    """
    
    if request.method == 'POST':
        try:
            # Parse form data
            title = request.form.get('title')
            description = request.form.get('description')
            event_date = datetime.strptime(request.form.get('event_date'), '%Y-%m-%d').date()
            start_time = datetime.strptime(request.form.get('start_time'), '%H:%M').time()
            end_time = datetime.strptime(request.form.get('end_time'), '%H:%M').time()
            location = request.form.get('location')
            capacity = int(request.form.get('capacity'))
            
            # Validate
            if not all([title, event_date, start_time, end_time, location, capacity]):
                flash('All required fields must be filled', 'danger')
                return redirect(url_for('admin.create_event'))
            
            if capacity <= 0:
                flash('Capacity must be greater than 0', 'danger')
                return redirect(url_for('admin.create_event'))
            
            if start_time >= end_time:
                flash('End time must be after start time', 'danger')
                return redirect(url_for('admin.create_event'))
            
            # Create event
            event = Event(
                title=title,
                description=description,
                event_date=event_date,
                start_time=start_time,
                end_time=end_time,
                location=location,
                capacity=capacity,
                created_by=current_user.id,
                status=Event.STATUS_DRAFT
            )
            
            db.session.add(event)
            db.session.commit()
            
            flash(f'Event "{title}" created successfully!', 'success')
            logger.info(f"Event created by admin {current_user.email}: {title}")
            return redirect(url_for('admin.event_detail', event_id=event.id))
        
        except ValueError as e:
            flash(f'Invalid input: {str(e)}', 'danger')
            logger.error(f"Validation error creating event: {str(e)}")
            return redirect(url_for('admin.create_event'))
        
        except Exception as e:
            db.session.rollback()
            flash('Error creating event. Please try again.', 'danger')
            logger.exception(f"Error creating event: {str(e)}")
            return redirect(url_for('admin.create_event'))
    
    return render_template('admin/create_event.html')


@admin_bp.route('/events/<int:event_id>')
@login_required
@admin_only
def event_detail(event_id):
    """
    View and edit event details.
    
    Shows:
    - Event information
    - Registered volunteers
    - Pending approvals
    - Attendance statistics
    """
    
    event = Event.query.get_or_404(event_id)
    
    # Get registrations by status
    pending = EventRegistration.query.filter_by(
        event_id=event_id,
        registration_status=EventRegistration.STATUS_PENDING
    ).all()
    
    approved = EventRegistration.query.filter_by(
        event_id=event_id,
        registration_status=EventRegistration.STATUS_APPROVED
    ).all()
    
    attended = Attendance.query.filter_by(event_id=event_id).all()
    
    return render_template(
        'admin/event_detail.html',
        event=event,
        pending_registrations=pending,
        approved_registrations=approved,
        attendances=attended
    )


@admin_bp.route('/registrations/<int:registration_id>/approve', methods=['POST'])
@login_required
@admin_only
def approve_registration(registration_id):
    """
    Approve a volunteer's event registration.
    
    Checks event capacity before approving.
    """
    
    registration = EventRegistration.query.get_or_404(registration_id)
    event = registration.event
    
    # Check capacity
    if not event.has_capacity():
        flash('Event is at full capacity. Cannot approve.', 'danger')
        return redirect(url_for('admin.event_detail', event_id=event.id))
    
    try:
        registration.approve(current_user.id)
        flash(
            f'Approved {registration.volunteer.first_name} for {event.title}',
            'success'
        )
        logger.info(
            f"Registration approved by {current_user.email}: "
            f"{registration.volunteer.email} for {event.title}"
        )
    except Exception as e:
        flash('Error approving registration. Please try again.', 'danger')
        logger.exception(f"Error approving registration: {str(e)}")
    
    return redirect(url_for('admin.event_detail', event_id=event.id))


@admin_bp.route('/registrations/<int:registration_id>/reject', methods=['POST'])
@login_required
@admin_only
def reject_registration(registration_id):
    """
    Reject a volunteer's event registration.
    """
    
    registration = EventRegistration.query.get_or_404(registration_id)
    event = registration.event
    
    reason = request.form.get('reason', 'Not selected')
    
    try:
        registration.reject(current_user.id, reason)
        flash(
            f'Rejected {registration.volunteer.first_name} for {event.title}',
            'success'
        )
        logger.info(
            f"Registration rejected by {current_user.email}: "
            f"{registration.volunteer.email} for {event.title}"
        )
    except Exception as e:
        flash('Error rejecting registration. Please try again.', 'danger')
        logger.exception(f"Error rejecting registration: {str(e)}")
    
    return redirect(url_for('admin.event_detail', event_id=event.id))


@admin_bp.route('/events/<int:event_id>/publish', methods=['POST'])
@login_required
@admin_only
def publish_event(event_id):
    """
    Publish an event (change status from draft to published).
    """
    
    event = Event.query.get_or_404(event_id)
    
    try:
        event.publish()
        flash(f'Event "{event.title}" published!', 'success')
        logger.info(f"Event published by {current_user.email}: {event.title}")
    except Exception as e:
        flash('Error publishing event. Please try again.', 'danger')
        logger.exception(f"Error publishing event: {str(e)}")
    
    return redirect(url_for('admin.event_detail', event_id=event.id))


@admin_bp.route('/events/<int:event_id>/cancel', methods=['POST'])
@login_required
@admin_only
def cancel_event(event_id):
    """
    Cancel an event.
    """
    
    event = Event.query.get_or_404(event_id)
    
    try:
        event.cancel()
        flash(f'Event "{event.title}" cancelled!', 'success')
        logger.info(f"Event cancelled by {current_user.email}: {event.title}")
    except Exception as e:
        flash('Error cancelling event. Please try again.', 'danger')
        logger.exception(f"Error cancelling event: {str(e)}")
    
    return redirect(url_for('admin.events'))