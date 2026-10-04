import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    String, Boolean, Integer, Float, Text, ForeignKey, 
    DateTime, UniqueConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.types import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


def generate_uuid() -> uuid.UUID:
    return uuid.uuid4()


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="candidate", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, onupdate=now_utc, nullable=False)

    jobs = relationship("Job", back_populates="user", cascade="all, delete-orphan")
    resumes = relationship("Resume", back_populates="user", cascade="all, delete-orphan")
    interviews = relationship("Interview", back_populates="user", cascade="all, delete-orphan")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    company: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    raw_content: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="ready", nullable=False)  # pending, ready, failed
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, onupdate=now_utc, nullable=False)

    user = relationship("User", back_populates="jobs")
    analysis = relationship("JobAnalysis", back_populates="job", uselist=False, cascade="all, delete-orphan")


class JobAnalysis(Base):
    __tablename__ = "job_analyses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), unique=True, nullable=False)
    role_title: Mapped[str] = mapped_column(String(200), nullable=False)
    seniority: Mapped[str] = mapped_column(String(50), nullable=False)
    required_skills: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    preferred_skills: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    technical_competencies: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    behavioral_competencies: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    responsibilities: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    experience_expectations: Mapped[str] = mapped_column(Text, default="", nullable=False)
    important_keywords: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    domain_knowledge: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)

    job = relationship("Job", back_populates="analysis")


class Resume(Base):
    __tablename__ = "resumes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    file_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    candidate_name: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    skills: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    experience_years: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    education: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="ready", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, onupdate=now_utc, nullable=False)

    user = relationship("User", back_populates="resumes")
    claims = relationship("ResumeClaim", back_populates="resume", cascade="all, delete-orphan")


class ResumeClaim(Base):
    __tablename__ = "resume_claims"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    resume_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True)
    claim_text: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)  # scale, metric, architecture, tooling, leadership
    evidence: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.9, nullable=False)
    importance: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    interview_priority: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    outcome: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # confirmed, exaggerated, refuted
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)

    resume = relationship("Resume", back_populates="claims")


class JobFitResult(Base):
    __tablename__ = "job_fit_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    resume_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False)
    overall_score: Mapped[float] = mapped_column(Float, nullable=False)
    classification: Mapped[str] = mapped_column(String(50), nullable=False)  # STRONG_FIT, GOOD_FIT, MODERATE_FIT, POOR_FIT
    dimension_scores: Mapped[Dict[str, float]] = mapped_column(JSON, nullable=False)
    matched_skills: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    partial_matches: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    missing_skills: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    preparation_gaps: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.92, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)

    __table_args__ = (
        UniqueConstraint("job_id", "resume_id", name="uq_job_resume_fit"),
    )


class Interview(Base):
    __tablename__ = "interviews"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    resume_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="CREATED", nullable=False)
    configuration: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    target_duration_minutes: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="interviews")
    state = relationship("InterviewState", back_populates="interview", uselist=False, cascade="all, delete-orphan")
    questions = relationship("InterviewQuestion", back_populates="interview", cascade="all, delete-orphan", order_by="InterviewQuestion.sequence_number")
    report = relationship("InterviewReport", back_populates="interview", uselist=False, cascade="all, delete-orphan")
    preparation_plan = relationship("PreparationPlan", back_populates="interview", uselist=False, cascade="all, delete-orphan")


class InterviewState(Base):
    __tablename__ = "interview_states"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    interview_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("interviews.id", ondelete="CASCADE"), unique=True, nullable=False)
    current_level: Mapped[str] = mapped_column(String(50), default="screening", nullable=False)  # screening, competency, deep_dive
    difficulty: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    question_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    topics_covered: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    topics_remaining: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    strong_topics: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    weak_topics: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    claims_to_probe: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    time_remaining_seconds: Mapped[int] = mapped_column(Integer, default=1800, nullable=False)
    version_id: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, onupdate=now_utc, nullable=False)

    interview = relationship("Interview", back_populates="state")


class InterviewQuestion(Base):
    __tablename__ = "interview_questions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    interview_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("interviews.id", ondelete="CASCADE"), nullable=False, index=True)
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)
    level: Mapped[str] = mapped_column(String(50), nullable=False)
    competency: Mapped[str] = mapped_column(String(100), nullable=False)
    difficulty: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    strategy: Mapped[str] = mapped_column(String(100), default="explore", nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    target_claim_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    time_limit_seconds: Mapped[int] = mapped_column(Integer, default=180, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)

    interview = relationship("Interview", back_populates="questions")
    answer = relationship("Answer", back_populates="question", uselist=False, cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("interview_id", "sequence_number", name="uq_interview_question_sequence"),
    )


class Answer(Base):
    __tablename__ = "answers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    question_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("interview_questions.id", ondelete="CASCADE"), unique=True, nullable=False)
    transcript: Mapped[str] = mapped_column(Text, nullable=False)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    speaking_pace_wpm: Mapped[int] = mapped_column(Integer, default=130, nullable=False)
    filler_word_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    pause_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    longest_pause_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)

    question = relationship("InterviewQuestion", back_populates="answer")
    evaluation = relationship("AnswerEvaluation", back_populates="answer", uselist=False, cascade="all, delete-orphan")


class AnswerEvaluation(Base):
    __tablename__ = "answer_evaluations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    answer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("answers.id", ondelete="CASCADE"), unique=True, nullable=False)
    overall_score: Mapped[float] = mapped_column(Float, nullable=False)
    relevance_score: Mapped[float] = mapped_column(Float, default=7.0, nullable=False)
    correctness_score: Mapped[float] = mapped_column(Float, default=7.0, nullable=False)
    depth_score: Mapped[float] = mapped_column(Float, default=7.0, nullable=False)
    communication_score: Mapped[float] = mapped_column(Float, default=7.0, nullable=False)
    reasoning_score: Mapped[float] = mapped_column(Float, default=7.0, nullable=False)
    assessment: Mapped[str] = mapped_column(String(50), default="SATISFACTORY", nullable=False)
    strengths: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    weaknesses: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    missing_points: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    follow_up_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)

    answer = relationship("Answer", back_populates="evaluation")


class InterviewReport(Base):
    __tablename__ = "interview_reports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    interview_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("interviews.id", ondelete="CASCADE"), unique=True, nullable=False)
    overall_score: Mapped[float] = mapped_column(Float, nullable=False)
    role_fit: Mapped[float] = mapped_column(Float, nullable=False)
    technical_knowledge: Mapped[float] = mapped_column(Float, nullable=False)
    problem_solving: Mapped[float] = mapped_column(Float, nullable=False)
    communication: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    depth: Mapped[float] = mapped_column(Float, nullable=False)
    behavioral_fit: Mapped[float] = mapped_column(Float, nullable=False)
    readiness_classification: Mapped[str] = mapped_column(String(50), nullable=False)  # NOT_READY, NEEDS_PREPARATION, INTERVIEW_READY, STRONG_CANDIDATE
    strengths: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    weaknesses: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    question_feedback: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)

    interview = relationship("Interview", back_populates="report")


class PreparationPlan(Base):
    __tablename__ = "preparation_plans"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    interview_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("interviews.id", ondelete="CASCADE"), unique=True, nullable=False)
    priority: Mapped[str] = mapped_column(String(50), default="high", nullable=False)
    items: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)

    interview = relationship("Interview", back_populates="preparation_plan")


class AIRequest(Base):
    __tablename__ = "ai_requests"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    request_id: Mapped[str] = mapped_column(String(100), nullable=False)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    operation: Mapped[str] = mapped_column(String(100), nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    input_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    estimated_cost_usd: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="success", nullable=False)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    fallback_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)
