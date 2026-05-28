"""All database models."""
from sqlalchemy import (
    Column, String, Text, Boolean, DateTime, Integer,
    ForeignKey, Enum, JSON, Float
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import uuid
import enum


# ─── ENUMS ────────────────────────────────────────────────────────

class UserRole(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"

class DocumentType(str, enum.Enum):
    POLICY = "policy"
    REJECTION_LETTER = "rejection_letter"
    DISCHARGE_SUMMARY = "discharge_summary"
    HOSPITAL_BILL = "hospital_bill"
    INSURER_LETTER = "insurer_letter"
    OTHER = "other"

class ClaimStatus(str, enum.Enum):
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    REJECTED = "rejected"
    APPEALING = "appealing"
    RESOLVED = "resolved"
    ESCALATED = "escalated"

class AppealType(str, enum.Enum):
    GRO = "gro"                    # Grievance Redressal Officer
    INSURER = "insurer_escalation"
    OMBUDSMAN = "ombudsman"
    BIMA_BHAROSA = "bima_bharosa"
    CONSUMER_COURT = "consumer_court"

class InsuranceType(str, enum.Enum):
    HEALTH = "health"
    MOTOR = "motor"


# ─── MODELS ──────────────────────────────────────────────────────
# Order matters for FK resolution: User → Claim → Document → Appeal

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone = Column(String(15), unique=True, nullable=True)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    documents = relationship("Document", back_populates="owner", cascade="all, delete-orphan")
    claims = relationship("Claim", back_populates="owner", cascade="all, delete-orphan")
    appeals = relationship("Appeal", back_populates="owner", cascade="all, delete-orphan")


class Claim(Base):
    __tablename__ = "claims"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    policy_number = Column(String(100), nullable=True)
    insurer_name = Column(String(255), nullable=False)
    claim_amount = Column(Float, nullable=True)
    insurance_type = Column(Enum(InsuranceType), nullable=False)
    status = Column(Enum(ClaimStatus), default=ClaimStatus.SUBMITTED)

    # Rejection details
    rejection_reason_raw = Column(Text, nullable=True)      # original text from letter
    rejection_reason_parsed = Column(JSON, nullable=True)   # structured: {category, rule_violated}
    irdai_violation = Column(Boolean, nullable=True)        # did insurer violate IRDAI rules?
    irdai_violation_details = Column(JSON, nullable=True)
    audit_report = Column(JSON, nullable=True)              # full structured audit

    # Timelines (IRDAI mandated)
    claim_date = Column(DateTime(timezone=True), nullable=True)
    rejection_date = Column(DateTime(timezone=True), nullable=True)
    gro_deadline = Column(DateTime(timezone=True), nullable=True)   # +15 days from rejection
    irdai_deadline = Column(DateTime(timezone=True), nullable=True) # +30 days from GRO

    # Notification flags
    gro_reminder_sent = Column(Boolean, default=False)
    irdai_reminder_sent = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    owner = relationship("User", back_populates="claims")
    documents = relationship("Document", back_populates="claim")
    appeals = relationship("Appeal", back_populates="claim", cascade="all, delete-orphan")


class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    claim_id = Column(UUID(as_uuid=True), ForeignKey("claims.id"), nullable=True)
    file_name = Column(String(500), nullable=False)
    file_path = Column(String(1000), nullable=False)   # MinIO path
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    doc_type = Column(Enum(DocumentType), nullable=False)
    insurance_type = Column(Enum(InsuranceType), nullable=True)

    # Processing state
    ocr_status = Column(String(50), default="pending")  # pending|processing|done|failed
    ocr_text = Column(Text, nullable=True)
    embedding_status = Column(String(50), default="pending")

    # AI Analysis results
    extracted_clauses = Column(JSON, nullable=True)   # structured clause data
    risk_flags = Column(JSON, nullable=True)          # list of risky conditions
    summary = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    owner = relationship("User", back_populates="documents")
    claim = relationship("Claim", back_populates="documents")


class Appeal(Base):
    __tablename__ = "appeals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    claim_id = Column(UUID(as_uuid=True), ForeignKey("claims.id"), nullable=False)
    appeal_type = Column(Enum(AppealType), nullable=False)

    # Generated letter content
    letter_content = Column(Text, nullable=True)
    letter_html = Column(Text, nullable=True)
    legal_references = Column(JSON, nullable=True)   # list of IRDAI regulations cited

    # Status tracking
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    response_deadline = Column(DateTime(timezone=True), nullable=True)
    response_received = Column(Boolean, default=False)
    outcome = Column(String(100), nullable=True)  # approved|rejected|partial|pending

    # Generation metadata
    model_used = Column(String(100), nullable=True)
    generation_time_ms = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    owner = relationship("User", back_populates="appeals")
    claim = relationship("Claim", back_populates="appeals")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False)
    resource_type = Column(String(100), nullable=True)
    resource_id = Column(String(100), nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    extra = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())