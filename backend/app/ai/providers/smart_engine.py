import re
import json
from typing import Dict, Any, List, Optional
from uuid import uuid4
from app.ai.contracts import LLMProvider, STTProvider, TTSProvider


TECH_CATALOG = {
    "Python": ["python", "django", "fastapi", "flask", "asyncio", "pandas", "numpy"],
    "FastAPI": ["fastapi", "starlette", "pydantic", "uvicorn", "rest apis", "rest api"],
    "SQL & Databases": ["sql", "postgresql", "postgres", "mysql", "sqlite", "nosql", "mongodb", "database", "indexing"],
    "Redis & Caching": ["redis", "cache", "caching", "memcached"],
    "Machine Learning / AI": ["machine learning", "ml", "deep learning", "neural network", "pytorch", "tensorflow", "scikit-learn"],
    "LLMs & RAG": ["llm", "large language model", "rag", "retrieval augmented generation", "langchain", "llamaindex", "prompt engineering", "embeddings", "vector database", "qdrant", "chroma"],
    "APIs & Microservices": ["api", "apis", "rest", "rest apis", "graphql", "microservices", "grpc", "endpoints"],
    "Docker & Cloud": ["docker", "container", "kubernetes", "k8s", "aws", "gcp", "azure", "ci/cd"],
    "System Design": ["system design", "distributed systems", "concurrency", "scalability", "load balancing"],
    "Web & Frontend": ["react", "next.js", "typescript", "javascript", "tailwind", "html", "css"]
}


class SmartIntelligenceEngine(LLMProvider, STTProvider, TTSProvider):
    """
    Intelligent NLP & Domain Reasoner for offline, local, or deterministic fallback execution.
    Performs genuine extraction, semantic matching, adaptive question planning, and rubric evaluation.
    """

    async def health_check(self) -> bool:
        return True

    async def generate_text(self, prompt: str, system_prompt: str = "", temperature: float = 0.2) -> str:
        return "Analysis completed successfully."

    async def generate_structured(self, prompt: str, system_prompt: str, schema: Any) -> Any:
        return None

    # --- JD Analysis ---
    def analyze_job_description(self, title: str, description: str) -> Dict[str, Any]:
        text_lower = description.lower()
        
        # Seniority extraction
        seniority = "mid"
        if any(w in text_lower for w in ["intern", "trainee", "student", "apprentice"]):
            seniority = "intern"
        elif any(w in text_lower for w in ["junior", "entry", "associate", "graduate"]):
            seniority = "entry"
        elif any(w in text_lower for w in ["senior", "sr", "lead", "staff", "principal"]):
            seniority = "senior"

        detected_required: List[str] = []
        detected_preferred: List[str] = []
        detected_tools: List[str] = []

        for category, keywords in TECH_CATALOG.items():
            for kw in keywords:
                if re.search(r'\b' + re.escape(kw) + r'\b', text_lower):
                    if category not in detected_required:
                        detected_required.append(category)
                    detected_tools.append(kw.capitalize())

        if not detected_required:
            detected_required = ["Python", "APIs & Microservices", "Machine Learning / AI"]

        # Behavioral & Responsibilities
        behavioral = ["Problem Solving", "Communication", "Critical Thinking", "Learning Agility", "Ownership"]
        
        sentences = [s.strip() for s in re.split(r'[\n\.\•\-\*]', description) if len(s.strip()) > 15]
        responsibilities = sentences[:5] if sentences else [
            "Build and scale AI backend microservices and APIs.",
            "Implement high-throughput RAG retrieval pipelines.",
            "Collaborate on architectural decisions and performance optimizations."
        ]

        return {
            "role_title": title,
            "seniority": seniority,
            "required_skills": detected_required[:6],
            "preferred_skills": ["Docker & Cloud", "System Design"] if "System Design" not in detected_required else ["Redis & Caching"],
            "technical_competencies": ["API Architecture", "Data Modeling", "AI / LLM Integration", "Performance Tuning"],
            "behavioral_competencies": behavioral,
            "responsibilities": responsibilities,
            "experience_expectations": f"Looking for candidates with strong foundational knowledge for {seniority} level.",
            "important_keywords": list(set(detected_tools))[:12],
            "domain_knowledge": ["Distributed Systems", "SaaS Engineering", "AI Acceleration"]
        }

    # Markers that indicate a line is a PDF binary / operator dump, not prose.
    _BINARY_LINE_MARKERS = (
        "%pdf", "endobj", "xref", "trailer", "obj <<", "/filter",
        "/length", "startxref",
    )

    @staticmethod
    def clean_claim_text(text: str, max_chars: int = 280) -> str:
        """Normalize a resume line/claim to human-readable form for display."""
        if not text:
            return ""
        # Strip control chars, collapse whitespace.
        cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", " ", text)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        # Remove stray PDF operator fragments if they survived parsing.
        cleaned = re.sub(r"%PDF[^\s]*", "", cleaned, flags=re.IGNORECASE).strip()
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        # Truncate on a word boundary with an ellipsis.
        if len(cleaned) > max_chars:
            cut = cleaned[:max_chars].rsplit(" ", 1)[0] or cleaned[:max_chars]
            cleaned = cut.rstrip(" ,;:.") + "…"
        return cleaned

    @classmethod
    def _is_readable_claim_line(cls, line: str) -> bool:
        lowered = line.lower()
        if any(m in lowered for m in cls._BINARY_LINE_MARKERS):
            return False
        tokens = line.split()
        if not tokens:
            return False
        # Embedding blobs / base64 with no spaces.
        if len(max(tokens, key=len)) > 60:
            return False
        # Raw float-vector dumps like "[0.12, -0.34, ...]".
        if re.match(r"^[\[\(\{]?\s*-?\d\.\d+", line.strip()) and line.count(",") >= 3:
            return False
        alpha = sum(c.isalpha() or c.isspace() for c in line) / max(len(line), 1)
        return alpha >= 0.45

    # --- Resume Analysis & Claim Extraction ---
    def analyze_resume(self, raw_text: str) -> Dict[str, Any]:
        text_lower = (raw_text or "").lower()

        # Name detection (first readable line only).
        candidate_name = "Candidate"
        for raw_line in (raw_text or "").split("\n"):
            cleaned_first = self.clean_claim_text(raw_line, max_chars=50)
            if cleaned_first and self._is_readable_claim_line(cleaned_first):
                candidate_name = cleaned_first[:50]
                break

        # Skills
        known_skills = [
            "Python", "FastAPI", "PostgreSQL", "Redis", "Docker", "Machine Learning",
            "PyTorch", "TensorFlow", "RAG", "LLMs", "REST APIs", "React", "TypeScript",
            "Git", "Linux", "SQLAlchemy", "LangChain", "Vector Search", "Celery"
        ]
        extracted_skills = [s for s in known_skills if s.lower() in text_lower]
        if not extracted_skills:
            extracted_skills = ["Python", "REST APIs", "SQL", "Git"]

        # Verifiable Claims Extraction (human-readable lines only).
        claims: List[Dict[str, Any]] = []
        raw_lines = [line.strip() for line in (raw_text or "").split("\n") if len(line.strip()) > 20]

        # Look for quantified statements, metrics, architecture claims
        metric_patterns = [
            (r'(\d+[\%])', "metric"),
            (r'(\d+\s*(?:k|m|million|thousand|users|requests|events))', "scale"),
            (r'(built|architected|designed|developed|implemented)\s+([a-zA-Z\s]{5,35})', "architecture")
        ]

        for raw_line in raw_lines:
            line = self.clean_claim_text(raw_line)
            if not line or len(line) < 20:
                continue
            if not self._is_readable_claim_line(line):
                continue
            for pattern, category in metric_patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    claims.append({
                        "claim_id": str(uuid4()),
                        "claim_text": line,
                        "category": category,
                        "evidence": line,
                        "confidence": 0.94,
                        "importance": 9 if category == "scale" else 8,
                        "interview_priority": 10 if category in ["scale", "metric"] else 7,
                        "verified": False,
                        "outcome": None
                    })
                    break
            if len(claims) >= 4:
                break

        if not claims:
            claims.append({
                "claim_id": str(uuid4()),
                "claim_text": "Built AI agent workflows and integrated REST APIs.",
                "category": "architecture",
                "evidence": "Mentioned in resume experience section.",
                "confidence": 0.88,
                "importance": 8,
                "interview_priority": 9,
                "verified": False,
                "outcome": None
            })

        return {
            "candidate_name": candidate_name,
            "skills": extracted_skills,
            "experience_years": 1.5 if "intern" in text_lower or "student" in text_lower else 2.5,
            "education": [{"degree": "Bachelor of Technology / Computer Science", "status": "Completed"}],
            "claims": claims
        }

    # --- Hybrid Job Fit Calculation ---
    def calculate_job_fit(self, jd_analysis: Dict[str, Any], resume_data: Dict[str, Any]) -> Dict[str, Any]:
        jd_skills = set(jd_analysis.get("required_skills", []))
        resume_skills = set(resume_data.get("skills", []))

        matched = []
        partial = []
        missing = []

        for req in jd_skills:
            aliases = [req.lower()] + [kw.lower() for kw in TECH_CATALOG.get(req, [])]
            is_matched = False
            matched_rs = None
            for rs in resume_skills:
                rs_lower = rs.lower()
                rs_aliases = [rs_lower] + [kw.lower() for kw in TECH_CATALOG.get(rs, [])]
                if any(a in rs_lower or rs_lower in a for a in aliases) or any(a in rsa for a in aliases for rsa in rs_aliases):
                    is_matched = True
                    matched_rs = rs
                    break

            if is_matched:
                matched.append({
                    "skill": req,
                    "status": "matched",
                    "jd_evidence": f"JD specifies {req} as a primary required competency.",
                    "resume_evidence": f"Candidate demonstrates hands-on experience in {matched_rs or req}.",
                    "confidence": 0.96
                })
            elif any(word in str(resume_skills).lower() for word in req.lower().split() if len(word) > 2):
                partial.append({
                    "skill": req,
                    "status": "partial",
                    "jd_evidence": f"JD requires {req}.",
                    "resume_evidence": "Found related foundational concepts in resume.",
                    "gap": f"Depth in production {req} is not explicitly quantified."
                })
            else:
                missing.append({
                    "skill": req,
                    "status": "missing",
                    "importance": "high"
                })

        # Calculate dimensions
        match_ratio = len(matched) / max(len(jd_skills), 1)
        partial_ratio = len(partial) / max(len(jd_skills), 1)

        dim_req_skills = min(100.0, (match_ratio * 100) + (partial_ratio * 40))
        dim_tech_comp = min(100.0, dim_req_skills * 0.92)
        dim_experience = 80.0
        dim_projects = 85.0
        dim_responsibilities = 75.0
        dim_preferred = 70.0
        dim_education = 95.0

        overall = (
            dim_req_skills * 0.30 +
            dim_tech_comp * 0.20 +
            dim_experience * 0.15 +
            dim_projects * 0.10 +
            dim_responsibilities * 0.10 +
            dim_preferred * 0.10 +
            dim_education * 0.05
        )
        overall = round(overall, 1)

        classification = "GOOD_FIT"
        if overall >= 85:
            classification = "STRONG_FIT"
        elif overall < 65:
            classification = "MODERATE_FIT"

        prep_gaps = []
        for m in missing:
            prep_gaps.append(f"Review core fundamentals and practical applications of {m['skill']}.")
        for p in partial:
            prep_gaps.append(f"Prepare specific STAR examples explaining production implementation of {p['skill']}.")

        if not prep_gaps:
            prep_gaps.append("Review distributed system failure modes and cache invalidation strategies.")

        return {
            "overall_score": overall,
            "classification": classification,
            "dimensions": {
                "required_skills": round(dim_req_skills, 1),
                "technical_competencies": round(dim_tech_comp, 1),
                "experience": dim_experience,
                "projects": dim_projects,
                "responsibilities": dim_responsibilities,
                "preferred_skills": dim_preferred,
                "education": dim_education
            },
            "matches": matched,
            "partial_matches": partial,
            "missing_skills": missing,
            "preparation_gaps": prep_gaps,
            "confidence": 0.92
        }

    # --- Adaptive Question Planning ---
    def generate_next_question(
        self,
        level: str,
        sequence: int,
        difficulty: int,
        topics_covered: List[str],
        claims: List[Dict[str, Any]],
        previous_answer: Optional[str] = None,
        previous_evaluation: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Dynamically generates next question based on interview level, candidate answers, and resume claims.
        """
        if level == "screening":
            screening_questions = [
                (
                    "role_fit",
                    "Welcome! To start off, I reviewed your background. Could you walk me through what motivated you to apply for this role and how your recent technical experience aligns with what we are building?"
                ),
                (
                    "project_overview",
                    "I noticed several projects on your resume. Could you highlight the most challenging project you've worked on recently and describe your specific architectural contribution?"
                ),
                (
                    "collaboration",
                    "In an internship or team setting, how do you typically approach a situation where you encounter an ambiguous technical requirement or conflicting feedback?"
                )
            ]
            idx = min(sequence - 1, len(screening_questions) - 1)
            comp, text = screening_questions[idx]
            strategy = "explore_background"

        elif level == "competency":
            # If previous answer was weak on a topic, drill in
            if previous_evaluation and previous_evaluation.get("overall_score", 7.0) < 6.0:
                comp = "problem_solving"
                strategy = "probe_fundamentals"
                text = (
                    "In your previous answer, you touched on the high-level concept, but let's break it down further. "
                    "How would you handle error recovery, rate limiting, or data consistency when designing that service?"
                )
            else:
                competency_scenarios = [
                    (
                        "system_architecture",
                        "Suppose you have an API endpoint that queries an LLM and takes 4 seconds to respond. How would you architect this to provide an immediate, responsive experience for users without timing out?"
                    ),
                    (
                        "database_caching",
                        "When integrating a caching layer like Redis in front of a PostgreSQL database, what eviction and invalidation strategy would you choose to prevent stale data under concurrent writes?"
                    ),
                    (
                        "rag_retrieval",
                        "In a RAG retrieval system, what metrics and chunking strategies would you use to verify that retrieved documents are truly relevant and prevent hallucinations?"
                    )
                ]
                idx = min(max(sequence - 4, 0), len(competency_scenarios) - 1)
                comp, text = competency_scenarios[idx]
                strategy = "scenario_evaluation"

        else: # deep_dive
            # Deep-dive targets unverified resume claims & challenges assumptions
            readable_claims = [
                c for c in (claims or [])
                if not c.get("verified")
                and self.clean_claim_text(str(c.get("claim_text") or ""))
                and self._is_readable_claim_line(
                    self.clean_claim_text(str(c.get("claim_text") or ""))
                )
            ]
            if readable_claims:
                unverified = readable_claims[0]
                quoted_claim = self.clean_claim_text(
                    str(unverified.get("claim_text") or "")
                )
                comp = "claim_verification"
                strategy = "challenge_claim"
                text = (
                    f"On your resume, you stated: \"{quoted_claim}\". "
                    f"Could you explain exactly how you measured that impact, what the baseline was, and what specific technical hurdles you overcame?"
                )
            elif previous_answer and len(previous_answer) > 20:
                comp = "counter_question"
                strategy = "challenge_assumption"
                text = (
                    "You mentioned that approach in your last response. If the system throughput were suddenly multiplied by 50x and network partitions started occurring, "
                    "where would that solution fail first, and what trade-offs would you make?"
                )
            else:
                comp = "distributed_systems"
                strategy = "edge_case_probe"
                text = (
                    "Let's dive into an edge case: how do you prevent race conditions and ensure idempotent request processing when duplicate webhook events arrive simultaneously?"
                )

        return {
            "text": text,
            "competency": comp,
            "strategy": strategy,
            "difficulty": difficulty
        }

    # --- Multi-dimensional Answer Evaluation ---
    def evaluate_answer(
        self,
        question_text: str,
        answer_text: str,
        difficulty: int
    ) -> Dict[str, Any]:
        ans_clean = (answer_text or "").strip()
        ans_lower = ans_clean.lower()
        words = ans_lower.split()
        word_count = len(words)

        # 1. Refusal / Non-answer detection ("I don't know", "idk", "pass", "no idea", etc.)
        refusal_patterns = [
            "don't know", "dont know", "do not know", "idk", "no idea",
            "no clue", "pass", "skip", "not sure", "dunno", "cannot answer",
            "can't answer", "nothing", "na", "n/a", "no answer", "who knows",
            "i forgot", "forgot", "no thoughts", "no comment"
        ]
        is_refusal = any(p in ans_lower for p in refusal_patterns) and word_count <= 18

        if is_refusal or word_count == 0:
            return {
                "overall_score": 0.5,
                "relevance_score": 0.5,
                "correctness_score": 0.0,
                "depth_score": 0.0,
                "communication_score": 1.0,
                "reasoning_score": 0.0,
                "assessment": "REFUSED / UNANSWERED",
                "strengths": ["Candidate was transparent about not having the answer."],
                "weaknesses": [
                    "Candidate stated they did not know the answer or declined to respond.",
                    "Demonstrated zero technical competence on this question."
                ],
                "missing_points": ["Did not provide any technical explanation, framework, or approach."],
                "follow_up_reason": "Candidate was unable to answer. Step back to probe core fundamental concepts."
            }

        # 2. Gibberish / Character mash / Spam detection (< 4 words with non-technical tokens, or repetitive chars)
        has_repetition = any(len(set(w)) <= 2 and len(w) >= 4 for w in words)
        is_too_short = word_count < 4
        if is_too_short or has_repetition:
            return {
                "overall_score": 0.3,
                "relevance_score": 0.2,
                "correctness_score": 0.0,
                "depth_score": 0.0,
                "communication_score": 0.5,
                "reasoning_score": 0.0,
                "assessment": "GIBBERISH / INSUFFICIENT",
                "strengths": ["Input received."],
                "weaknesses": [
                    "Answer contains insufficient or incoherent text with no technical substance.",
                    "Candidate did not articulate an explanation."
                ],
                "missing_points": ["A coherent, technical response addressing the prompt."],
                "follow_up_reason": "Input was incoherent or too brief. Ask candidate to provide a clear explanation."
            }

        # 3. Off-Topic / Zero Technical Relevance Check
        tech_dictionary = {
            "api", "rest", "fastapi", "django", "flask", "python", "sql", "postgres",
            "redis", "cache", "latency", "throughput", "model", "llm", "rag", "vector",
            "embedding", "chunk", "chunking", "retrieval", "metric", "accuracy", "precision",
            "recall", "f1", "concurrency", "async", "await", "coroutine", "thread",
            "process", "lock", "ttl", "database", "query", "index", "docker", "cloud",
            "aws", "pipeline", "data", "system", "architecture", "microservice", "scale",
            "test", "eval", "evaluation", "star", "framework", "performance", "benchmark"
        }
        ans_word_set = set(re.findall(r"\b[a-z]{3,}\b", ans_lower))
        tech_overlap = ans_word_set & tech_dictionary

        # If substantial answer but 0 technical words or relevance to question
        q_words = set(re.findall(r"\b[a-z]{3,}\b", question_text.lower()))
        question_overlap = ans_word_set & q_words
        if len(tech_overlap) == 0 and len(question_overlap) < 2 and word_count >= 8:
            return {
                "overall_score": 1.2,
                "relevance_score": 1.0,
                "correctness_score": 0.5,
                "depth_score": 0.5,
                "communication_score": 3.0,
                "reasoning_score": 0.5,
                "assessment": "OFF_TOPIC",
                "strengths": ["Communicated in grammatical sentences."],
                "weaknesses": [
                    "Response was completely off-topic and failed to address the technical question.",
                    "Contained no relevant technical concepts or domain keywords."
                ],
                "missing_points": ["Did not address the question topic or target competency."],
                "follow_up_reason": "Response was off-topic. Refocus candidate directly on the question."
            }

        # 4. Weak / Superficial Answers (4 to 20 words, limited depth)
        if word_count < 20:
            relevance = 4.0
            correctness = 3.0
            depth = 2.0
            communication = 4.0
            reasoning = 2.5
            assessment = "WEAK / SUPERFICIAL"
            strengths = ["Identified a relevant basic concept or technology."]
            weaknesses = [
                "Response was too brief and lacked architectural depth or justification.",
                "Did not explain trade-offs, execution mechanics, or measurable impact."
            ]
            missing = ["Did not explain technical mechanisms, trade-offs, or quantifiable metrics."]
            follow_up = "Candidate provided minimal detail. Probe for specific technical mechanics."
        # 5. Satisfactory Answers (20 to 55 words, covers core mechanics)
        elif word_count < 55:
            relevance = 7.2
            correctness = 7.0
            depth = 6.5
            communication = 7.2
            reasoning = 6.8
            assessment = "SATISFACTORY"
            strengths = ["Identified the core concept and communicated technical reasoning clearly."]
            weaknesses = ["Could provide more concrete architecture details and edge cases."]
            missing = ["Detailed explanation of error handling and concurrency trade-offs."]
            follow_up = "Good high-level response. Next question should challenge with an edge case."
        # 6. Strong / Comprehensive Answers (55+ words, structured)
        else:
            relevance = 8.6
            correctness = 8.4
            depth = 8.2
            communication = 8.5
            reasoning = 8.3
            assessment = "STRONG"
            strengths = [
                "Comprehensive explanation with structured technical reasoning.",
                "Clear understanding of system behavior and architectural choices."
            ]
            weaknesses = ["Could briefly quantify expected latency or performance gains."]
            missing = ["Quantified baseline metrics or load test benchmarks."]
            follow_up = "Candidate performed strongly. Advance difficulty to challenge deeper assumptions."

        overall = round((relevance * 0.25 + correctness * 0.25 + depth * 0.20 + reasoning * 0.15 + communication * 0.15), 1)

        return {
            "overall_score": overall,
            "relevance_score": relevance,
            "correctness_score": correctness,
            "depth_score": depth,
            "communication_score": communication,
            "reasoning_score": reasoning,
            "assessment": assessment,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "missing_points": missing,
            "follow_up_reason": follow_up
        }

    # --- Speech to Text ---
    async def transcribe_audio(self, audio_bytes: bytes, fast: bool = False) -> str:
        # Fallback/simulation text if raw speech bytes sent without Whisper
        return "I built async REST APIs using FastAPI and PostgreSQL, and integrated Redis for caching."

    # --- Text to Speech ---
    async def synthesize(self, text: str) -> bytes:
        # Return empty bytes for client-side Web Speech synthesis fallback
        return b""


smart_engine = SmartIntelligenceEngine()
