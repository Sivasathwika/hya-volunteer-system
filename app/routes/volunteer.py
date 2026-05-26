"""
Volunteer routes - Dashboard, profile management, event viewing.

Routes:
- GET /volunteer/dashboard → Show volunteer dashboard with stats
- GET /volunteer/profile → Show volunteer profile
- POST /volunteer/profile → Update volunteer profile
- GET /volunteer/skills → Show skills
- POST /volunteer/skills/add → Add skill
- GET /volunteer/events → List registered events
- GET /volunteer/certificates → List earned certificates

Design:
- All routes require @login_required
- Most require @volunteer_only
- Services handle business logic
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.database import db
from app.models import Volunteer, Skill, Event, EventRegistration, Certificate, Attendance
from app.utils.decorators import volunteer_only
from sqlalchemy import func
import logging

logger = logging.getLogger(__name__)

volunteer_bp = Blueprint('volunteer', __name__, url_prefix='/volunteer')


@volunteer_bp.route('/dashboard')
@login_required
@volunteer_only
def dashboard():
    """
    Volunteer dashboard - Overview of participation and stats.
    
    Shows:
    - Total hours volunteered
    - Events attended
    - Certificates earned
    - Upcoming registered events
    - Recent activity
    """
    
    volunteer = current_user
    
    # Calculate stats
    total_hours = db.session.query(func.sum(Attendance.hours_served)).filter_by(
        volunteer_id=volunteer.id
    ).scalar() or 0
    
    events_attended = Attendance.query.filter_by(volunteer_id=volunteer.id).count()
    
    certificates = Certificate.query.filter_by(volunteer_id=volunteer.id).count()
    
    # Get upcoming registered events
    upcoming_events = db.session.query(Event, EventRegistration).join(
        EventRegistration, Event.id == EventRegistration.event_id
    ).filter(
        EventRegistration.volunteer_id == volunteer.id,
        EventRegistration.registration_status == EventRegistration.STATUS_APPROVED
    ).all()
    
    # Get recent certificates
    recent_certificates = Certificate.query.filter_by(
        volunteer_id=volunteer.id
    ).order_by(Certificate.issued_date.desc()).limit(5).all()
    
    stats = {
        'total_hours': round(total_hours, 1),
        'events_attended': events_attended,
        'certificates': certificates
    }
    
    return render_template(
        'volunteer/dashboard.html',
        stats=stats,
        upcoming_events=upcoming_events,
        recent_certificates=recent_certificates
    )


@volunteer_bp.route('/profile', methods=['GET', 'POST'])
@login_required
@volunteer_only
def profile():
    """
    Volunteer profile - View and edit profile information.
    
    GET: Show profile form
    POST: Update profile (city, state, bio)
    """
    
    volunteer = current_user
    
    if request.method == 'POST':
        # Update profile
        volunteer.first_name = request.form.get('first_name', volunteer.first_name)
        volunteer.last_name = request.form.get('last_name', volunteer.last_name)
        volunteer.phone = request.form.get('phone', volunteer.phone)
        volunteer.city = request.form.get('city', volunteer.city)
        volunteer.state = request.form.get('state', volunteer.state)
        volunteer.bio = request.form.get('bio', volunteer.bio)
        
        # Mark profile as complete if all required fields are filled
        if all([volunteer.first_name, volunteer.last_name, volunteer.city, volunteer.state]):
            volunteer.profile_complete = True
        
        try:
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            logger.info(f"Profile updated for volunteer: {volunteer.email}")
            return redirect(url_for('volunteer.profile'))
        except Exception as e:
            db.session.rollback()
            logger.exception(f"Error updating profile: {str(e)}")
            flash('Error updating profile. Please try again.', 'danger')
    
    return render_template('volunteer/profile.html', volunteer=volunteer)


@volunteer_bp.route('/skills')
@login_required
@volunteer_only
def skills():
    """
    View volunteer's skills.
    
    Shows:
    - All skills with proficiency level
    - Years of experience
    - Option to add/remove skills
    """
    
    volunteer = current_user
    volunteer_skills = volunteer.skills.all()
    
    # Get all available skills for the "add skill" dropdown
    all_skills = Skill.query.all()
    
    # Get skills already added
    added_skill_ids = {vs.skill_id for vs in volunteer_skills}
    available_skills = [s for s in all_skills if s.id not in added_skill_ids]
    
    return render_template(
        'volunteer/skills.html',
        volunteer_skills=volunteer_skills,
        available_skills=available_skills
    )


@volunteer_bp.route('/skills/add', methods=['POST'])
@login_required
@volunteer_only
def add_skill():
    """
    Add a skill to volunteer profile.
    
    POST data:
    - skill_id: ID of skill to add
    - proficiency_level: beginner, intermediate, expert
    - years_of_experience: Number of years
    """
    
    volunteer = current_user
    skill_id = request.form.get('skill_id', type=int)
    proficiency = request.form.get('proficiency_level', 'beginner')
    years = request.form.get('years_of_experience', type=int, default=0)
    
    if not skill_id:
        flash('Please select a skill', 'danger')
        return redirect(url_for('volunteer.skills'))
    
    skill = Skill.query.get(skill_id)
    if not skill:
        flash('Skill not found', 'danger')
        return redirect(url_for('volunteer.skills'))
    
    try:
        volunteer.add_skill(skill, proficiency, years)
        flash(f'Added skill: {skill.name}', 'success')
        logger.info(f"Skill added for volunteer {volunteer.email}: {skill.name}")
    except Exception as e:
        flash(f'Error adding skill: {str(e)}', 'danger')
        logger.exception(f"Error adding skill: {str(e)}")
    
    return redirect(url_for('volunteer.skills'))


@volunteer_bp.route('/skills/<int:skill_id>/remove', methods=['POST'])
@login_required
@volunteer_only
def remove_skill(skill_id):
    """Remove a skill from volunteer profile."""
    
    volunteer = current_user
    skill = Skill.query.get(skill_id)
    
    if not skill:
        flash('Skill not found', 'danger')
        return redirect(url_for('volunteer.skills'))
    
    try:
        volunteer.remove_skill(skill)
        flash(f'Removed skill: {skill.name}', 'success')
        logger.info(f"Skill removed for volunteer {volunteer.email}: {skill.name}")
    except Exception as e:
        flash(f'Error removing skill: {str(e)}', 'danger')
        logger.exception(f"Error removing skill: {str(e)}")
    
    return redirect(url_for('volunteer.skills'))


@volunteer_bp.route('/events')
@login_required
@volunteer_only
def events():
    """
    List events volunteer has registered for or attended.
    
    Shows:
    - Pending approvals
    - Approved events
    - Past events attended
    - Certificates earned
    """
    
    volunteer = current_user
    
    # Get all registrations for this volunteer
    registrations = EventRegistration.query.filter_by(
        volunteer_id=volunteer.id
    ).all()
    
    # Organize by status
    pending = [r for r in registrations if r.registration_status == EventRegistration.STATUS_PENDING]
    approved = [r for r in registrations if r.registration_status == EventRegistration.STATUS_APPROVED]
    attended = [r for r in registrations if r.registration_status == EventRegistration.STATUS_ATTENDED]
    
    return render_template(
        'volunteer/events.html',
        pending_registrations=pending,
        approved_registrations=approved,
        attended_registrations=attended
    )


@volunteer_bp.route('/certificates')
@login_required
@volunteer_only
def certificates():
    """
    View certificates earned by volunteer.
    
    Shows:
    - All certificates with dates
    - Links to download PDFs
    - Verification codes
    """
    
    volunteer = current_user
    certificates = Certificate.query.filter_by(
        volunteer_id=volunteer.id
    ).order_by(Certificate.issued_date.desc()).all()
    
    return render_template('volunteer/certificates.html', certificates=certificates)


@volunteer_bp.route('/certificates/<int:cert_id>/download')
@login_required
@volunteer_only
def download_certificate(cert_id):
    """Download certificate PDF."""
    
    certificate = Certificate.query.get_or_404(cert_id)
    
    # Check ownership
    if certificate.volunteer_id != current_user.id:
        flash('You do not have permission to download this certificate', 'danger')
        return redirect(url_for('volunteer.certificates'))
    
    # TODO: Implement PDF download
    # For now, just redirect to certificate page
    flash('Certificate download feature coming soon', 'info')
    return redirect(url_for('volunteer.certificates'))