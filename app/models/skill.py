"""
Skill models - Normalized skill tracking for volunteers.

Design:
- Skill: Lookup table (Python, WebDevelopment, etc.) - stored once
- VolunteerSkill: Junction table - links volunteers to skills with proficiency level

Why not store skills as JSON in Volunteer?
- Not queryable: "Find volunteers with Python" requires parsing JSON
- Not normalized: Skill name stored in 1000 rows (redundant)
- Not scalable: JSON parsing is slower than indexed queries
- Bad practice: Production systems always normalize lookups

Performance: Proper indexing makes this fast.
"""

from app.database import BaseModel, db


class Skill(BaseModel):
    """
    Skill lookup table.
    
    Columns:
    - id: Primary key
    - name: Skill name (e.g., "Python", "Web Design")
    - category: Skill category for organization
    - created_at, updated_at: Audit fields
    
    Indexed on name for fast lookups.
    """
    
    __tablename__ = 'skills'
    
    # Columns
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    category = db.Column(db.String(100), index=True)  # e.g., "Programming", "Design"
    
    # Relationships
    # Many-to-many with Volunteer through VolunteerSkill
    volunteers = db.relationship(
        'VolunteerSkill',
        backref='skill',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    
    def __repr__(self):
        return f"<Skill {self.name} ({self.category})>"
    
    def __str__(self):
        return self.name
    
    @classmethod
    def get_by_name(cls, name: str):
        """Query skill by name (case-insensitive)."""
        return cls.query.filter_by(name=name.lower()).first()
    
    @classmethod
    def get_or_create(cls, name: str, category: str = None):
        """
        Get existing skill or create if doesn't exist.
        Useful in forms/imports.
        """
        skill = cls.get_by_name(name)
        if not skill:
            skill = cls(name=name.lower(), category=category)
            db.session.add(skill)
            db.session.commit()
        return skill
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category
        }


class VolunteerSkill(BaseModel):
    """
    Junction table linking Volunteer to Skill with additional metadata.
    
    Columns:
    - volunteer_id: Foreign key to Volunteer
    - skill_id: Foreign key to Skill
    - proficiency_level: 'beginner', 'intermediate', or 'expert'
    - years_of_experience: How many years doing this skill
    
    Composite unique constraint: A volunteer can have each skill only once.
    """
    
    __tablename__ = 'volunteer_skills'
    
    # Foreign keys
    volunteer_id = db.Column(
        db.Integer,
        db.ForeignKey('volunteers.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    skill_id = db.Column(
        db.Integer,
        db.ForeignKey('skills.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    
    # Proficiency level
    proficiency_level = db.Column(
        db.String(50),
        default='beginner',
        nullable=False
    )
    
    # Experience
    years_of_experience = db.Column(db.Integer, default=0, nullable=False)
    
    # Composite unique constraint: Volunteer can't have same skill twice
    __table_args__ = (
        db.UniqueConstraint('volunteer_id', 'skill_id', name='uq_volunteer_skill'),
    )
    
    def __repr__(self):
        return f"<VolunteerSkill {self.volunteer.email} - {self.skill.name}>"
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'skill_id': self.skill_id,
            'skill_name': self.skill.name,
            'proficiency_level': self.proficiency_level,
            'years_of_experience': self.years_of_experience
        }