"""
Donation model - Track monetary donations with verification.

Design:
- volunteer_id is NULLABLE (anonymous donations)
- event_id is NULLABLE (general donations not tied to event)
- Status workflow: pending → verified → failed

Why separate event and volunteer?
- Some donations are general (to the organization)
- Some are event-specific (fundraiser at event)
- Some donors want to remain anonymous
"""

from app.database import BaseModel, db
from datetime import datetime


class Donation(BaseModel):
    """
    Donation tracking with verification workflow.
    
    Columns:
    - volunteer_id: Who donated (nullable for anonymous)
    - event_id: Associated event (nullable for general donations)
    - amount: Donation amount
    - currency: Currency code (default INR for India)
    - upi_qr_code: QR code for payment (blob/image)
    - donation_status: 'pending' | 'verified' | 'failed' | 'refunded'
    - verified_by: Which admin verified
    - verified_at: When verified
    - payment_reference: External payment ID (for reconciliation)
    """
    
    __tablename__ = 'donations'
    
    # Status constants
    STATUS_PENDING = 'pending'
    STATUS_VERIFIED = 'verified'
    STATUS_FAILED = 'failed'
    STATUS_REFUNDED = 'refunded'
    VALID_STATUSES = [STATUS_PENDING, STATUS_VERIFIED, STATUS_FAILED, STATUS_REFUNDED]
    
    # Foreign keys (both nullable)
    volunteer_id = db.Column(
        db.Integer,
        db.ForeignKey('volunteers.id'),
        index=True
    )
    event_id = db.Column(
        db.Integer,
        db.ForeignKey('events.id'),
        index=True
    )
    
    # Donation details
    amount = db.Column(db.Numeric(10, 2), nullable=False)  # Up to 99,999.99
    currency = db.Column(db.String(3), default='INR', nullable=False)
    
    # QR code for payment (stored as blob or file path)
    upi_qr_code = db.Column(db.LargeBinary)  # Binary data of QR code image
    
    # Workflow
    donation_status = db.Column(
        db.String(50),
        default=STATUS_PENDING,
        nullable=False,
        index=True
    )
    verified_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    verified_at = db.Column(db.DateTime)
    
    # For reconciliation with payment gateway
    payment_reference = db.Column(db.String(255), unique=True, index=True)
    
    def __repr__(self):
        donor = self.donor.email if self.donor else "Anonymous"
        return f"<Donation {self.amount} {self.currency} from {donor}>"
    
    def verify(self, admin_id: int):
        """Admin verifies donation received."""
        self.donation_status = self.STATUS_VERIFIED
        self.verified_by = admin_id
        self.verified_at = datetime.utcnow()
        db.session.commit()
    
    def mark_failed(self):
        """Mark donation as failed (e.g., payment declined)."""
        self.donation_status = self.STATUS_FAILED
        db.session.commit()
    
    def refund(self):
        """Mark donation as refunded."""
        self.donation_status = self.STATUS_REFUNDED
        db.session.commit()
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'volunteer_id': self.volunteer_id,
            'event_id': self.event_id,
            'amount': float(self.amount),
            'currency': self.currency,
            'status': self.donation_status,
            'verified_at': self.verified_at.isoformat() if self.verified_at else None,
            'payment_reference': self.payment_reference,
            'created_at': self.created_at.isoformat()
        }