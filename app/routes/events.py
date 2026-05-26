"""
Event routes - Public event listing and volunteer registration.

Routes:
- GET /events → List published events with filters
- GET /events/<id> → Event details
- POST /events/<id>/register → Register for event
- POST /events/<id>/unregister → Cancel registration

Design:
- Event listing is public (no login required)
- Registration requires login and volunteer role
- Services handle approval workflow
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.database import db
from app.models import Event, EventRegistration, Volunteer, Attendance
from app.utils.decorators import volunteer_only
from datetime import date
from sqlalchemy import func
import logging

logger = logging.getLogger(__name__)

events_bp = Blueprint('events', __name__, url_prefix='/events')


@events_bp.route('/')
def list_events():
    """
    List all published events.
    
    Query parameters:
    - page: Pagination page number
    - status: Filter by status (published, ongoing, completed)
    - city: Filter by location
    - search: Search in title/description
    """
    
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', 'published')
    city = request.args.get('city', '')
    search = request.args.get('search', '')
    
    query = Event.query
    
    # Filter by status
    if status and status in Event.VALID_STATUSES:
        query = query.filter_by(status=status)
    else:
        query = query.filter_by(status=Event.STATUS_PUBLISHED)
    
    # Filter by city
    if city:
        query = query.filter(Event.location.ilike(f'%{city}%'))
    
    # Search in title and description
    if search:
        query = query.filter(
            (Event.title.ilike(f'%{search}%')) |
            (Event.description.ilike(f'%{search}%'))
        )
    
    # Order by date
    events = query.order_by(Event.event_date).paginate(page=page, per_page=12)
    
    # Get list of cities for filter dropdown
    cities = db.session.query(func.distinct(Event.location)).all()
    cities = [c[0] for c in cities if c[0]]
    
    return render_template(
        'events/list.html',
        events=events,
        cities=cities,
        selected_city=city,
        search_query=search,
        selected_status=status
    )


@events_bp.route('/<int:event_id>')
def event_detail(event_id):
    """
    View event details.
    
    Shows:
    - Event information
    - Current capacity
    - Registered volunteer count
    - Available actions (register/unregister)
    """
    
    event = Event.query.get_or_404(event_id)
    
    # Check if published (or user is admin)
    if event.status == Event.STATUS_DRAFT:
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('Event not found', 'danger')
            return redirect(url_for('events.list_events'))
    
    # Get registration stats
    approved_count = EventRegistration.query.filter_by(
        event_id=event_id,
        registration_status=EventRegistration.STATUS_APPROVED
    ).count()
    
    # Check if current user is registered
    user_registration = None
    if current_user.is_authenticated and current_user.is_volunteer():
        user_registration = EventRegistration.query.filter_by(
            event_id=event_id,
            volunteer_id=current_user.id
        ).first()
    
    return render_template(
        'events/detail.html',
        event=event,
        approved_count=approved_count,
        user_registration=user_registration
    )


@events_bp.route('/<int:event_id>/register', methods=['POST'])
@login_required
@volunteer_only
def register_event(event_id):
    """
    Register volunteer for an event.
    
    Creates EventRegistration with status=pending (awaiting admin approval).
    """
    
    event = Event.query.get_or_404(event_id)
    volunteer = current_user
    
    # Check if already registered
    existing = EventRegistration.query.filter_by(
        event_id=event_id,
        volunteer_id=volunteer.id
    ).first()
    
    if existing:
        if existing.registration_status == EventRegistration.STATUS_REJECTED:
            flash('Your registration was rejected. You cannot register again.', 'danger')
        else:
            flash('You are already registered for this event.', 'info')
        return redirect(url_for('events.event_detail', event_id=event_id))
    
    try:
        # Create registration (status=pending by default)
        registration = EventRegistration(
            volunteer_id=volunteer.id,
            event_id=event_id,
            registration_status=EventRegistration.STATUS_PENDING
        )
        
        db.session.add(registration)
        db.session.commit()
        
        flash(
            f'You have registered for "{event.title}". '
            'Your registration is pending admin approval.',
            'success'
        )
        logger.info(
            f"Volunteer {volunteer.email} registered for event {event.title}"
        )
        
    except Exception as e:
        db.session.rollback()
        flash('Error registering for event. Please try again.', 'danger')
        logger.exception(f"Error registering volunteer: {str(e)}")
    
    return redirect(url_for('events.event_detail', event_id=event_id))


@events_bp.route('/<int:event_id>/unregister', methods=['POST'])
@login_required
@volunteer_only
def unregister_event(event_id):
    """
    Cancel registration for an event.
    
    Only allows cancellation if status is pending or approved (not attended).
    """
    
    event = Event.query.get_or_404(event_id)
    volunteer = current_user
    
    registration = EventRegistration.query.filter_by(
        event_id=event_id,
        volunteer_id=volunteer.id
    ).first()
    
    if not registration:
        flash('You are not registered for this event.', 'info')
        return redirect(url_for('events.event_detail', event_id=event_id))
    
    # Cannot cancel if already attended
    if registration.registration_status == EventRegistration.STATUS_ATTENDED:
        flash('Cannot cancel. You have already attended this event.', 'danger')
        return redirect(url_for('events.event_detail', event_id=event_id))
    
    try:
        db.session.delete(registration)
        db.session.commit()
        
        flash(f'Your registration for "{event.title}" has been cancelled.', 'success')
        logger.info(
            f"Volunteer {volunteer.email} unregistered from event {event.title}"
        )
        
    except Exception as e:
        db.session.rollback()
        flash('Error cancelling registration. Please try again.', 'danger')
        logger.exception(f"Error unregistering volunteer: {str(e)}")
    
    return redirect(url_for('events.event_detail', event_id=event_id))