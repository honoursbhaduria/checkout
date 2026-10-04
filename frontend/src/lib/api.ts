const API_BASE = "http://localhost:8000/api/v1";

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: string;
}

export interface JobAnalysis {
  role_title: string;
  seniority: string;
  required_skills: string[];
  preferred_skills: string[];
  technical_competencies: string[];
  behavioral_competencies: string[];
  responsibilities: string[];
  experience_expectations: string;
  important_keywords: string[];
  domain_knowledge: string[];
}

export interface Job {
  id: string;
  title: string;
  company?: string;
  content_hash: string;
  status: string;
  analysis?: JobAnalysis;
}

export interface ResumeClaim {
  id: string;
  claim_text: string;
  category: string;
  evidence: string;
  confidence: number;
  importance: number;
  interview_priority: number;
  verified: boolean;
}

export interface ResumeChunk {
  chunk_index: number;
  text: string;
  section: string;
  char_count: number;
}

export interface Resume {
  id: string;
  candidate_name?: string;
  skills: string[];
  experience_years: number;
  claims: ResumeClaim[];
  file_url?: string;
  chunks_indexed?: number;
  chunks?: ResumeChunk[];
  vector_collection?: string;
}

export interface SkillMatch {
  skill: string;
  status: "matched" | "partial" | "missing";
  jd_evidence?: string;
  resume_evidence?: string;
  confidence?: number;
  gap?: string;
}

export interface JobFitResult {
  job_fit_id: string;
  overall_score: number;
  classification: string;
  dimensions: {
    required_skills: number;
    technical_competencies: number;
    experience: number;
    projects: number;
    responsibilities: number;
    preferred_skills: number;
    education: number;
  };
  matches: SkillMatch[];
  partial_matches: SkillMatch[];
  missing_skills: { skill: string; importance: string }[];
  preparation_gaps: string[];
  confidence: number;
}

export interface QuestionData {
  question_id: string;
  sequence: number;
  level: "screening" | "competency" | "deep_dive" | string;
  question: {
    text: string;
    type: string;
    competency: string;
    difficulty: number;
  };
  response_mode: string;
  time_limit_seconds: number;
  state: {
    current_level: string;
    difficulty: number;
    topics_covered: string[];
    strong_topics: string[];
    weak_topics: string[];
    time_remaining_seconds: number;
    progress_percent: number;
  };
}

export interface AnswerEvaluation {
  evaluation_id: string;
  overall_score: number;
  scores: Record<string, number>;
  assessment: string;
  strengths: string[];
  weaknesses: string[];
  missing_points: string[];
  follow_up_reason?: string;
}

export interface ReportData {
  report_id: string;
  overall_score: number;
  role_fit: number;
  technical_knowledge: number;
  problem_solving: number;
  communication: number;
  confidence: number;
  depth: number;
  behavioral_fit: number;
  readiness: {
    classification: string;
    score: number;
    badge_color: string;
  };
  strengths: string[];
  weaknesses: string[];
  question_feedback: {
    question_id: string;
    sequence: number;
    question_text: string;
    candidate_answer: string;
    assessment: string;
    what_was_good: string;
    what_could_be_better: string;
    ideal_direction: string;
  }[];
}

export interface PreparationPlanData {
  plan_id: string;
  priority: string;
  items: {
    topic: string;
    priority: "high" | "medium" | "low";
    reason: string;
    current_level: number;
    target_level: number;
    estimated_minutes: number;
    action_items: string[];
  }[];
}

class ApiClient {
  private token: string | null = null;

  constructor() {
    this.token = localStorage.getItem("token");
  }

  setToken(token: string) {
    this.token = token;
    localStorage.setItem("token", token);
  }

  getToken(): string | null {
    return this.token || localStorage.getItem("token");
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...(options.headers as Record<string, string>),
    };

    const token = this.getToken();
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    const res = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers,
    });

    const json = await res.json();
    if (!res.ok || json.success === false) {
      throw new Error(json.error?.message || "An unexpected API error occurred");
    }

    return json.data as T;
  }

  async loginDemo(): Promise<{ user: User; token: string }> {
    const res = await this.request<any>("/auth/login", {
      method: "POST",
      body: JSON.stringify({
        email: "candidate@studentcredibility.com",
        password: "accelerator123",
      }),
    });
    this.setToken(res.tokens.access_token);
    return { user: res.user, token: res.tokens.access_token };
  }

  async createJob(title: string, description: string, company?: string): Promise<Job> {
    return this.request<Job>("/jobs", {
      method: "POST",
      body: JSON.stringify({ title, description, company }),
    });
  }

  async createResume(raw_text: string, candidate_name?: string): Promise<Resume> {
    return this.request<Resume>("/resumes", {
      method: "POST",
      body: JSON.stringify({ raw_text, candidate_name }),
    });
  }

  async uploadResumeFile(file: File, candidate_name?: string): Promise<Resume> {
    const formData = new FormData();
    formData.append("file", file);
    if (candidate_name) {
      formData.append("candidate_name", candidate_name);
    }
    const token = this.getToken();
    const headers: Record<string, string> = {};
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
    const res = await fetch(`${API_BASE}/resumes/upload`, {
      method: "POST",
      headers,
      body: formData,
    });
    const json = await res.json();
    if (!res.ok || json.success === false) {
      throw new Error(json.error?.message || "Failed to upload and parse resume file");
    }
    return json.data as Resume;
  }

  async calculateJobFit(job_id: string, resume_id: string): Promise<JobFitResult> {
    return this.request<JobFitResult>("/job-fit", {
      method: "POST",
      body: JSON.stringify({ job_id, resume_id }),
    });
  }

  async createInterview(job_id: string, resume_id: string, mode: string = "voice"): Promise<{ id: string }> {
    return this.request<{ id: string }>("/interviews", {
      method: "POST",
      body: JSON.stringify({
        job_id,
        resume_id,
        configuration: { mode, target_duration_minutes: 30 },
      }),
    });
  }

  async startInterview(interview_id: string): Promise<QuestionData> {
    return this.request<QuestionData>(`/interviews/${interview_id}/start`, {
      method: "POST",
    });
  }

  async getCurrentQuestion(interview_id: string): Promise<QuestionData> {
    return this.request<QuestionData>(`/interviews/${interview_id}/current-question`);
  }

  async submitAnswer(
    interview_id: string,
    question_id: string,
    transcript: string,
    duration_ms: number = 40000,
    wpm: number = 130
  ): Promise<AnswerEvaluation> {
    return this.request<AnswerEvaluation>(`/interviews/${interview_id}/answers`, {
      method: "POST",
      body: JSON.stringify({
        question_id,
        transcript,
        timing: { duration_ms },
        voice_metrics: { words_per_minute: wpm },
      }),
    });
  }

  async completeInterview(interview_id: string): Promise<any> {
    return this.request<any>(`/interviews/${interview_id}/complete`, {
      method: "POST",
    });
  }

  async getReport(interview_id: string): Promise<ReportData> {
    return this.request<ReportData>(`/interviews/${interview_id}/report`);
  }

  async getPreparationPlan(interview_id: string): Promise<PreparationPlanData> {
    return this.request<PreparationPlanData>(`/interviews/${interview_id}/preparation`);
  }

  async transcribeAudioFile(audioBlob: Blob): Promise<string> {
    const formData = new FormData();
    formData.append("file", audioBlob, "recording.webm");
    const token = this.getToken();
    const headers: Record<string, string> = {};
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
    const res = await fetch(`${API_BASE}/voice/transcribe-file`, {
      method: "POST",
      headers,
      body: formData,
    });
    const json = await res.json();
    if (!res.ok || json.success === false) {
      throw new Error(json.error?.message || "Failed to transcribe audio");
    }
    return json.data?.transcript || "";
  }
}

export const api = new ApiClient();
