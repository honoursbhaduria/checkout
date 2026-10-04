from datetime import datetime, timezone
from uuid import UUID
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from app.infrastructure.models.models import (
    Interview, InterviewState, InterviewQuestion, 
    Answer, AnswerEvaluation, Resume, Job, ResumeClaim
)
from app.domain.schemas import (
    InterviewCreate, InterviewResponse, QuestionResponse, 
    QuestionDetail, AnswerSubmitRequest, AnswerEvaluationResponse
)
from app.ai.router import ai_router
from app.core.exceptions import ResourceNotFoundError, StateConflictError


class InterviewService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.ai = ai_router.get_intelligence_engine()

    async def create_interview(self, user_id: UUID, data: InterviewCreate) -> InterviewResponse:
        # Verify job and resume ownership
        job_stmt = select(Job).where(Job.id == data.job_id, Job.user_id == user_id)
        job_res = await self.db.execute(job_stmt)
        if not job_res.scalar_one_or_none():
            raise ResourceNotFoundError("Job", str(data.job_id))

        resume_stmt = select(Resume).options(selectinload(Resume.claims)).where(
            Resume.id == data.resume_id, 
            Resume.user_id == user_id
        )
        resume_res = await self.db.execute(resume_stmt)
        resume = resume_res.scalar_one_or_none()
        if not resume:
            raise ResourceNotFoundError("Resume", str(data.resume_id))

        # Atomic transaction: Interview + Initial State
        interview = Interview(
            user_id=user_id,
            job_id=data.job_id,
            resume_id=data.resume_id,
            status="CREATED",
            configuration=data.configuration.model_dump() if data.configuration else {},
            target_duration_minutes=data.configuration.target_duration_minutes if data.configuration else 30
        )
        self.db.add(interview)
        await self.db.flush()

        claims_to_probe = [str(c.id) for c in (resume.claims or []) if c.interview_priority >= 7]

        initial_state = InterviewState(
            interview_id=interview.id,
            current_level="screening",
            difficulty=5,
            question_index=0,
            topics_covered=[],
            topics_remaining=["Role Fit", "Architecture", "Problem Solving", "Scale & Claims"],
            strong_topics=[],
            weak_topics=[],
            claims_to_probe=claims_to_probe,
            time_remaining_seconds=interview.target_duration_minutes * 60
        )
        self.db.add(initial_state)
        await self.db.commit()
        await self.db.refresh(interview)

        return InterviewResponse(
            id=interview.id,
            job_id=interview.job_id,
            resume_id=interview.resume_id,
            status=interview.status,
            configuration=interview.configuration,
            target_duration_minutes=interview.target_duration_minutes,
            created_at=interview.created_at,
            current_question=None
        )

    async def start_interview(self, user_id: UUID, interview_id: UUID) -> QuestionResponse:
        interview = await self._get_interview_entity(user_id, interview_id)
        if interview.status == "COMPLETED":
            raise StateConflictError("Interview has already been completed.")

        state = interview.state
        if state.question_index == 0:
            # Generate first screening question
            q_data = self.ai.generate_next_question(
                level="screening",
                sequence=1,
                difficulty=state.difficulty,
                topics_covered=state.topics_covered,
                claims=[]
            )

            question = InterviewQuestion(
                interview_id=interview.id,
                sequence_number=1,
                level="screening",
                competency=q_data["competency"],
                difficulty=q_data["difficulty"],
                strategy=q_data["strategy"],
                question_text=q_data["text"]
            )
            self.db.add(question)
            
            interview.status = "SCREENING"
            state.question_index = 1
            await self.db.commit()
            await self.db.refresh(question)
            return self._to_question_response(question, state)
        else:
            # Return current active question
            return await self.get_current_question(user_id, interview_id)

    async def get_current_question(self, user_id: UUID, interview_id: UUID) -> QuestionResponse:
        interview = await self._get_interview_entity(user_id, interview_id)
        state = interview.state

        q_stmt = select(InterviewQuestion).where(
            InterviewQuestion.interview_id == interview_id,
            InterviewQuestion.sequence_number == state.question_index
        )
        q_res = await self.db.execute(q_stmt)
        question = q_res.scalar_one_or_none()
        if not question:
            raise ResourceNotFoundError("Question", f"Sequence {state.question_index}")

        return self._to_question_response(question, state)

    async def submit_answer(self, user_id: UUID, interview_id: UUID, data: AnswerSubmitRequest) -> AnswerEvaluationResponse:
        interview = await self._get_interview_entity(user_id, interview_id)
        state = interview.state

        # Get Question
        q_stmt = select(InterviewQuestion).options(selectinload(InterviewQuestion.answer)).where(
            InterviewQuestion.id == data.question_id,
            InterviewQuestion.interview_id == interview_id
        )
        q_res = await self.db.execute(q_stmt)
        question = q_res.scalar_one_or_none()
        if not question:
            raise ResourceNotFoundError("Question", str(data.question_id))

        if question.answer:
            raise StateConflictError("An answer has already been submitted for this question.")

        # Record answer
        duration_ms = data.timing.duration_ms if data.timing else 45000
        answer = Answer(
            question_id=question.id,
            transcript=data.transcript,
            duration_ms=duration_ms,
            speaking_pace_wpm=data.voice_metrics.words_per_minute if data.voice_metrics else 130,
            filler_word_count=data.voice_metrics.filler_count if data.voice_metrics else 0,
            pause_count=data.voice_metrics.pause_count if data.voice_metrics else 0
        )
        self.db.add(answer)
        await self.db.flush()

        # Evaluate Answer
        eval_data = self.ai.evaluate_answer(
            question_text=question.question_text,
            answer_text=data.transcript,
            difficulty=question.difficulty
        )

        evaluation = AnswerEvaluation(
            answer_id=answer.id,
            overall_score=eval_data["overall_score"],
            relevance_score=eval_data["relevance_score"],
            correctness_score=eval_data["correctness_score"],
            depth_score=eval_data["depth_score"],
            communication_score=eval_data["communication_score"],
            reasoning_score=eval_data["reasoning_score"],
            assessment=eval_data["assessment"],
            strengths=eval_data["strengths"],
            weaknesses=eval_data["weaknesses"],
            missing_points=eval_data["missing_points"],
            follow_up_reason=eval_data["follow_up_reason"]
        )
        self.db.add(evaluation)

        # Update FSM State & Difficulty
        if eval_data["overall_score"] >= 8.0:
            state.difficulty = min(10, state.difficulty + 1)
            state.strong_topics = list(set(state.strong_topics + [question.competency]))
        elif eval_data["overall_score"] < 6.0:
            state.difficulty = max(2, state.difficulty - 1)
            state.weak_topics = list(set(state.weak_topics + [question.competency]))

        state.topics_covered = list(set(state.topics_covered + [question.competency]))
        state.time_remaining_seconds = max(0, state.time_remaining_seconds - (duration_ms // 1000))
        state.version_id += 1

        # Check Level Progression
        next_seq = question.sequence_number + 1
        if next_seq <= 3:
            state.current_level = "screening"
            interview.status = "SCREENING"
        elif next_seq <= 6:
            state.current_level = "competency"
            interview.status = "COMPLETED_SCREENING" if next_seq == 4 else "COMPETENCY"
        elif next_seq <= 9:
            state.current_level = "deep_dive"
            interview.status = "COMPLETED_COMPETENCY" if next_seq == 7 else "DEEP_DIVE"
        else:
            state.current_level = "finalizing"
            interview.status = "FINALIZING"

        # If not finalizing, prepare next question immediately
        if state.current_level != "finalizing":
            # Load resume claims for deep dive
            resume_stmt = select(Resume).options(selectinload(Resume.claims)).where(Resume.id == interview.resume_id)
            resume_res = await self.db.execute(resume_stmt)
            resume = resume_res.scalar_one_or_none()
            claims_dicts = [
                {"claim_id": str(c.id), "claim_text": c.claim_text, "verified": c.verified}
                for c in (resume.claims if resume else [])
            ]

            next_q_data = self.ai.generate_next_question(
                level=state.current_level,
                sequence=next_seq,
                difficulty=state.difficulty,
                topics_covered=state.topics_covered,
                claims=claims_dicts,
                previous_answer=data.transcript,
                previous_evaluation=eval_data
            )

            next_question = InterviewQuestion(
                interview_id=interview.id,
                sequence_number=next_seq,
                level=state.current_level,
                competency=next_q_data["competency"],
                difficulty=next_q_data["difficulty"],
                strategy=next_q_data["strategy"],
                question_text=next_q_data["text"]
            )
            self.db.add(next_question)
            state.question_index = next_seq

        await self.db.commit()
        await self.db.refresh(evaluation)

        return AnswerEvaluationResponse(
            evaluation_id=evaluation.id,
            answer_id=evaluation.answer_id,
            scores={
                "overall": evaluation.overall_score,
                "relevance": evaluation.relevance_score,
                "correctness": evaluation.correctness_score,
                "depth": evaluation.depth_score,
                "communication": evaluation.communication_score,
                "reasoning": evaluation.reasoning_score
            },
            overall_score=evaluation.overall_score,
            assessment=evaluation.assessment,
            strengths=evaluation.strengths,
            weaknesses=evaluation.weaknesses,
            missing_points=evaluation.missing_points,
            follow_up_reason=evaluation.follow_up_reason
        )

    async def complete_interview(self, user_id: UUID, interview_id: UUID) -> InterviewResponse:
        interview = await self._get_interview_entity(user_id, interview_id)
        interview.status = "COMPLETED"
        interview.completed_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(interview)

        return InterviewResponse(
            id=interview.id,
            job_id=interview.job_id,
            resume_id=interview.resume_id,
            status=interview.status,
            configuration=interview.configuration,
            target_duration_minutes=interview.target_duration_minutes,
            created_at=interview.created_at,
            current_question=None
        )

    async def _get_interview_entity(self, user_id: UUID, interview_id: UUID) -> Interview:
        stmt = select(Interview).options(selectinload(Interview.state)).where(
            Interview.id == interview_id,
            Interview.user_id == user_id
        )
        res = await self.db.execute(stmt)
        interview = res.scalar_one_or_none()
        if not interview:
            raise ResourceNotFoundError("Interview", str(interview_id))
        return interview

    def _to_question_response(self, question: InterviewQuestion, state: InterviewState) -> QuestionResponse:
        return QuestionResponse(
            question_id=question.id,
            sequence=question.sequence_number,
            level=question.level,
            question=QuestionDetail(
                text=question.question_text,
                type=question.strategy,
                competency=question.competency,
                difficulty=question.difficulty
            ),
            response_mode="voice",
            time_limit_seconds=question.time_limit_seconds,
            state={
                "current_level": state.current_level,
                "difficulty": state.difficulty,
                "topics_covered": state.topics_covered,
                "strong_topics": state.strong_topics,
                "weak_topics": state.weak_topics,
                "time_remaining_seconds": state.time_remaining_seconds,
                "progress_percent": int(min(100, (question.sequence_number / 9) * 100))
            }
        )
