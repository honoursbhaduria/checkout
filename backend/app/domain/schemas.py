from datetime import datetime, timezone
from typing import Generic, TypeVar, Optional, List, Dict, Any, Literal
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field

T = TypeVar("T")


# --- Standard API Envelopes ---
class Meta(BaseModel):
    request_id: str = "req_local"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    version: str = "v1"


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: List[Any] = []
    retryable: bool = False


class APIResponse(BaseModel, Generic[T]):
    success: bool = True
    data: Optional[T] = None
    meta: Meta = Field(default_factory=Meta)
    error: Optional[ErrorDetail] = None


# --- Authentication Schemas ---
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: str = Field(..., min_length=2)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: UUID
    email: str
    full_name: str
    role: str
    created_at: datetime


class TokenResponse(BaseModel):
    user: UserResponse
    tokens: Dict[str, Any]


class RefreshRequest(BaseModel):
    refresh_token: str


# --- Job Schemas ---
class JobCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=200)
    company: Optional[str] = None
    description: str = Field(..., min_length=20)
    source_url: Optional[str] = None


class JobAnalysisResponse(BaseModel):
    id: UUID
    job_id: UUID
    role_title: str
    seniority: str
    required_skills: List[str]
    preferred_skills: List[str]
    technical_competencies: List[str]
    behavioral_competencies: List[str]
    responsibilities: List[str]
    experience_expectations: str
    important_keywords: List[str]
    domain_knowledge: List[str]


class JobResponse(BaseModel):
    id: UUID
    title: str
    company: Optional[str]
    content_hash: str
    status: str
    created_at: datetime
    analysis: Optional[JobAnalysisResponse] = None


# --- Resume Schemas ---
class ResumeCreate(BaseModel):
    raw_text: str = Field(..., min_length=20)
    file_name: Optional[str] = None
    candidate_name: Optional[str] = None


class ResumeClaimResponse(BaseModel):
    id: UUID
    claim_text: str
    category: str
    evidence: str
    confidence: float
    importance: int
    interview_priority: int
    verified: bool
    outcome: Optional[str] = None


class ResumeResponse(BaseModel):
    id: UUID
    candidate_name: Optional[str]
    content_hash: str
    skills: List[str]
    experience_years: float
    status: str
    created_at: datetime
    claims: List[ResumeClaimResponse] = []


# --- Job Fit Schemas ---
class JobFitRequest(BaseModel):
    job_id: UUID
    resume_id: UUID
    options: Optional[Dict[str, bool]] = Field(default_factory=lambda: {"include_evidence": True, "include_gaps": True})


class SkillMatch(BaseModel):
    skill: str
    status: Literal["matched", "partial", "missing"]
    jd_evidence: Optional[str] = None
    resume_evidence: Optional[str] = None
    confidence: float = 0.95
    gap: Optional[str] = None


class JobFitResponse(BaseModel):
    job_fit_id: UUID
    job_id: UUID
    resume_id: UUID
    overall_score: float
    classification: str
    dimensions: Dict[str, float]
    matches: List[SkillMatch]
    partial_matches: List[SkillMatch]
    missing_skills: List[Dict[str, Any]]
    preparation_gaps: List[str]
    confidence: float


# --- Interview Schemas ---
class InterviewConfiguration(BaseModel):
    mode: Literal["voice", "text", "video"] = "voice"
    levels: List[str] = ["screening", "competency", "deep_dive"]
    difficulty: str = "adaptive"
    target_duration_minutes: int = 30
    interviewer_style: str = "professional"
    language: str = "en-US"


class InterviewCreate(BaseModel):
    job_id: UUID
    resume_id: UUID
    configuration: Optional[InterviewConfiguration] = Field(default_factory=InterviewConfiguration)


class QuestionDetail(BaseModel):
    text: str
    type: str = "scenario"
    competency: str
    difficulty: int


class QuestionResponse(BaseModel):
    question_id: UUID
    sequence: int
    level: str
    question: QuestionDetail
    response_mode: str = "voice"
    time_limit_seconds: int = 180
    state: Dict[str, Any]


class VoiceMetrics(BaseModel):
    words_per_minute: int = 130
    filler_count: int = 0
    pause_count: int = 0
    longest_pause_ms: int = 0


class AnswerTiming(BaseModel):
    started_at: Optional[str] = None
    ended_at: Optional[str] = None
    duration_ms: int = 0


class AnswerSubmitRequest(BaseModel):
    question_id: UUID
    transcript: str = Field(..., min_length=1)
    timing: Optional[AnswerTiming] = Field(default_factory=AnswerTiming)
    voice_metrics: Optional[VoiceMetrics] = Field(default_factory=VoiceMetrics)


class AnswerEvaluationResponse(BaseModel):
    evaluation_id: UUID
    answer_id: UUID
    scores: Dict[str, float]
    overall_score: float
    assessment: str
    strengths: List[str]
    weaknesses: List[str]
    missing_points: List[str]
    follow_up_reason: Optional[str] = None


class InterviewResponse(BaseModel):
    id: UUID
    job_id: UUID
    resume_id: UUID
    status: str
    configuration: Dict[str, Any]
    target_duration_minutes: int
    created_at: datetime
    current_question: Optional[QuestionResponse] = None


# --- Report & Preparation Schemas ---
class QuestionFeedbackItem(BaseModel):
    question_id: str
    sequence: int
    question_text: str
    candidate_answer: str
    assessment: str
    what_was_good: str
    what_could_be_better: str
    ideal_direction: str


class ReadinessDetail(BaseModel):
    classification: str
    score: float
    badge_color: str


class InterviewReportResponse(BaseModel):
    report_id: UUID
    interview_id: UUID
    overall_score: float
    role_fit: float
    technical_knowledge: float
    problem_solving: float
    communication: float
    confidence: float
    depth: float
    behavioral_fit: float
    readiness: ReadinessDetail
    strengths: List[str]
    weaknesses: List[str]
    question_feedback: List[QuestionFeedbackItem]


class PreparationItem(BaseModel):
    topic: str
    priority: Literal["high", "medium", "low"]
    reason: str
    current_level: int
    target_level: int
    estimated_minutes: int
    action_items: List[str]


class PreparationPlanResponse(BaseModel):
    plan_id: UUID
    interview_id: UUID
    priority: str
    items: List[PreparationItem]
