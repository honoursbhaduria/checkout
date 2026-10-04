import { useState, useEffect, useRef } from "react";
import confetti from "canvas-confetti";
import {
  Cpu,
  Terminal,
  Mic,
  Activity,
  Play,
  RotateCcw,
  Volume2,
  VolumeX,
  ArrowRight,
  AlertOctagon,
  Upload,
  Database,
  Layers,
  HardDrive,
  FileCheck,
  ChevronDown,
  ChevronUp,
  Sparkles,
  History,
  ThumbsUp,
  ThumbsDown,
} from "lucide-react";

import {
  api,
  type Job,
  type Resume,
  type JobFitResult,
  type QuestionData,
  type AnswerEvaluation,
  type ReportData,
  type PreparationPlanData,
  type InterviewHistorySummary,
} from "./lib/api";

import { IndustrialButton } from "./components/ui/IndustrialButton";
import { IndustrialCard } from "./components/ui/IndustrialCard";
import { IndustrialInput, IndustrialTextarea } from "./components/ui/IndustrialInput";
import { LedIndicator } from "./components/ui/LedIndicator";
import { OscilloscopeWave } from "./components/interview/OscilloscopeWave";
import { IndustrialMonitor } from "./components/interview/IndustrialMonitor";

const SAMPLE_JD = `Role: AI Engineer Intern / Associate Backend Engineer
Company: Student Credibility
Location: Remote / Hybrid

We are looking for an AI Engineer Intern to build next-generation career acceleration tools.
Key Responsibilities:
- Design high-performance asynchronous REST and WebSocket APIs using Python and FastAPI.
- Build and evaluate RAG pipelines using vector search and large language models.
- Implement intelligent prompt engineering and robust Pydantic schemas.
- Optimize low-latency caching layers using Redis and databases with PostgreSQL.

Required Skills:
- Python (FastAPI, AsyncIO, Pydantic)
- Machine Learning / AI fundamentals
- Large Language Models (LLMs) & RAG Architectures
- REST APIs & Microservices
- PostgreSQL & Relational DBs

Preferred:
- Redis & In-Memory Caching
- Docker & System Design`;

const SAMPLE_RESUME = `Honours Bhadauria
Email: honours.bhadauria@example.com | GitHub: github.com/honoursbhadauria

Summary:
Computer Science graduate with experience developing asynchronous backend services, RAG-powered conversational agents, and LLM applications in Python and FastAPI.

Technical Skills:
Python, FastAPI, PostgreSQL, Redis, Qdrant Vector Store, Docker, PyTorch, LangChain, REST APIs

Experience:
AI Backend Intern | Nexus AI Labs (2024)
- Architected an asynchronous REST API using FastAPI and PostgreSQL handling 15,000 requests per minute with sub-100ms response times.
- Integrated Redis for distributed session caching, reducing database query load by 40%.
- Improved model inference accuracy and retrieval latency by 18% through dynamic chunking and BM25 hybrid reranking.

Projects:
RAG-Powered Intelligent Document Copilot
- Built full-stack retrieval-augmented generation system indexing 500+ research papers in Qdrant vector database.
- Integrated streaming speech-to-text allowing real-time voice queries and answers.`;

const STORAGE_KEY = "checkout_industrial_interview_state_v1";

const getSavedState = () => {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) return JSON.parse(raw);
  } catch (e) {
    console.error("Failed to load saved state:", e);
  }
  return null;
};

export function App() {
  const saved = getSavedState();

  const [activeTab, setActiveTab] = useState<"ingest" | "role" | "fit" | "interview" | "report" | "history">(
    saved?.activeTab || "ingest"
  );
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Form states
  const [jdTitle, setJdTitle] = useState(saved?.jdTitle || "AI Engineer Intern");
  const [jdCompany, setJdCompany] = useState(saved?.jdCompany || "Student Credibility");
  const [jdText, setJdText] = useState(saved?.jdText || SAMPLE_JD);
  const [jdFile, setJdFile] = useState<File | null>(null);
  const [jdInputMode, setJdInputMode] = useState<"paste" | "upload">(saved?.jdInputMode || "paste");
  const [resumeText, setResumeText] = useState(saved?.resumeText || SAMPLE_RESUME);
  const [candidateName, setCandidateName] = useState(saved?.candidateName || "Honours Bhadauria");
  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [resumeInputMode, setResumeInputMode] = useState<"upload" | "paste">(saved?.resumeInputMode || "upload");
  const [showChunksDrawer, setShowChunksDrawer] = useState<boolean>(false);

  const [job, setJob] = useState<Job | null>(saved?.job || null);
  const [resume, setResume] = useState<Resume | null>(saved?.resume || null);
  const [jobFit, setJobFit] = useState<JobFitResult | null>(saved?.jobFit || null);

  // Interview simulator states
  const [interviewId, setInterviewId] = useState<string | null>(saved?.interviewId || null);
  const [currentQuestion, setCurrentQuestion] = useState<QuestionData | null>(saved?.currentQuestion || null);
  const [candidateAnswer, setCandidateAnswer] = useState<string>(saved?.candidateAnswer || "");
  const [latestEvaluation, setLatestEvaluation] = useState<AnswerEvaluation | null>(saved?.latestEvaluation || null);
  const [isSpeakingQuestion, setIsSpeakingQuestion] = useState<boolean>(false);
  const [isListeningMic, setIsListeningMic] = useState<boolean>(false);
  const [ttsEnabled, setTtsEnabled] = useState<boolean>(true);

  const recognitionRef = useRef<any>(null);
  const micStreamRef = useRef<MediaStream | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const liveIntervalRef = useRef<any>(null);
  const isTranscribingSliceRef = useRef<boolean>(false);
  const [isTranscribing, setIsTranscribing] = useState<boolean>(false);

  // Report states
  const [report, setReport] = useState<ReportData | null>(saved?.report || null);
  const [prepPlan, setPrepPlan] = useState<PreparationPlanData | null>(saved?.prepPlan || null);

  // History state
  const [historySummary, setHistorySummary] = useState<InterviewHistorySummary | null>(null);
  const [historyFilter, setHistoryFilter] = useState<"all" | "good" | "bad">("all");
  const [loadingHistory, setLoadingHistory] = useState<boolean>(false);

  // Synchronize state changes to localStorage so page refresh never loses progress
  useEffect(() => {
    try {
      const stateToPersist = {
        activeTab,
        job,
        resume,
        jobFit,
        interviewId,
        currentQuestion,
        candidateAnswer,
        latestEvaluation,
        report,
        prepPlan,
        jdTitle,
        jdCompany,
        jdText,
        candidateName,
        resumeText,
        jdInputMode,
        resumeInputMode,
      };
      localStorage.setItem(STORAGE_KEY, JSON.stringify(stateToPersist));
    } catch (e) {
      console.warn("Storage write error:", e);
    }
  }, [
    activeTab,
    job,
    resume,
    jobFit,
    interviewId,
    currentQuestion,
    candidateAnswer,
    latestEvaluation,
    report,
    prepPlan,
    jdTitle,
    jdCompany,
    jdText,
    candidateName,
    resumeText,
    jdInputMode,
    resumeInputMode,
  ]);

  const fetchHistory = async () => {
    try {
      setLoadingHistory(true);
      const summary = await api.getInterviewHistory();
      setHistorySummary(summary);
    } catch (e) {
      console.warn("Could not fetch interview history:", e);
    } finally {
      setLoadingHistory(false);
    }
  };

  useEffect(() => {
    api.loginDemo()
      .then(() => fetchHistory())
      .catch((e) => console.log("Demo auth init:", e));
  }, []);

  const handleResetSession = () => {
    if (window.confirm("RESET TELEMETRY SESSION: This will flush current job and resume cache to allow testing a new profile. Proceed?")) {
      try {
        localStorage.removeItem(STORAGE_KEY);
      } catch {}
      setJob(null);
      setResume(null);
      setJobFit(null);
      setInterviewId(null);
      setCurrentQuestion(null);
      setCandidateAnswer("");
      setLatestEvaluation(null);
      setReport(null);
      setPrepPlan(null);
      setActiveTab("ingest");
    }
  };

  const handleViewPastReport = async (pastInterviewId: string) => {
    try {
      setLoading(true);
      setError(null);
      const [pastReport, pastPlan] = await Promise.all([
        api.getReport(pastInterviewId),
        api.getPreparationPlan(pastInterviewId).catch(() => null),
      ]);
      setInterviewId(pastInterviewId);
      setReport(pastReport);
      setPrepPlan(pastPlan);
      setActiveTab("report");
      window.scrollTo({ top: 0, behavior: "smooth" });
    } catch (err: any) {
      setError(err.message || "Failed to load report for this interview");
    } finally {
      setLoading(false);
    }
  };

  const handleResumeInterview = async (pastInterviewId: string) => {
    try {
      setLoading(true);
      setError(null);
      const q = await api.getCurrentQuestion(pastInterviewId);
      setInterviewId(pastInterviewId);
      setCurrentQuestion(q);
      setActiveTab("interview");
      window.scrollTo({ top: 0, behavior: "smooth" });
    } catch (err: any) {
      setError(err.message || "Failed to resume interview");
    } finally {
      setLoading(false);
    }
  };

  const speakText = (text: string) => {
    if (!ttsEnabled || !("speechSynthesis" in window)) return;
    try {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 1.0;
      utterance.pitch = 0.95;
      utterance.lang = "en-US";

      const voices = window.speechSynthesis.getVoices();
      const voice = voices.find((v) => v.lang.startsWith("en") && (v.name.includes("Google") || v.name.includes("Natural") || v.name.includes("Samantha") || v.name.includes("David"))) || voices.find((v) => v.lang.startsWith("en"));
      if (voice) {
        utterance.voice = voice;
      }

      utterance.onstart = () => setIsSpeakingQuestion(true);
      utterance.onend = () => setIsSpeakingQuestion(false);
      utterance.onerror = () => setIsSpeakingQuestion(false);
      window.speechSynthesis.speak(utterance);
    } catch (e) {
      console.warn("TTS playback error:", e);
      setIsSpeakingQuestion(false);
    }
  };

  const startMicListening = async () => {
    setError(null);
    setCandidateAnswer("");

    let stream: MediaStream | null = null;
    try {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error("getUserMedia is not supported on this browser");
      }
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      micStreamRef.current = stream;
      setIsListeningMic(true);
      setError(null);

      try {
        audioChunksRef.current = [];
        const mime = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
          ? "audio/webm;codecs=opus"
          : MediaRecorder.isTypeSupported("audio/webm")
          ? "audio/webm"
          : MediaRecorder.isTypeSupported("audio/ogg")
          ? "audio/ogg"
          : "";
        const mr = mime ? new MediaRecorder(stream, { mimeType: mime }) : new MediaRecorder(stream);
        mr.ondataavailable = (e) => {
          if (e.data && e.data.size > 0) {
            audioChunksRef.current.push(e.data);
          }
        };
        mr.start(400);
        mediaRecorderRef.current = mr;

        // Live real-time audio transcription interval: sends accumulated audio slice every 1.5 seconds
        if (liveIntervalRef.current) clearInterval(liveIntervalRef.current);
        liveIntervalRef.current = setInterval(async () => {
          if (audioChunksRef.current.length >= 2 && !isTranscribingSliceRef.current) {
            const currentBlob = new Blob(audioChunksRef.current, { type: mr.mimeType || "audio/webm" });
            if (currentBlob.size > 800) {
              try {
                isTranscribingSliceRef.current = true;
                const partial = await api.transcribeAudioFile(currentBlob);
                if (partial && partial.trim()) {
                  setCandidateAnswer(partial.trim());
                }
              } catch (e) {
                console.warn("Live slice STT error:", e);
              } finally {
                isTranscribingSliceRef.current = false;
              }
            }
          }
        }, 1500);
      } catch (recErr) {
        console.warn("MediaRecorder setup notice:", recErr);
      }
    } catch (micErr: any) {
      console.warn("Microphone hardware access notice:", micErr);
      setIsListeningMic(false);
      if (micErr.name === "NotAllowedError" || micErr.name === "PermissionDeniedError") {
        setError("Microphone permission denied by browser. Please allow microphone in your URL bar, or click 'Quick Voice Sample'.");
      } else if (micErr.name === "NotFoundError" || micErr.name === "DevicesNotFoundError") {
        setError("Microphone hardware device not found. Please connect a microphone or click 'Quick Voice Sample'.");
      } else {
        setError(`Microphone access error (${micErr.name || "unavailable"}). Please use 'Quick Voice Sample' or type your response.`);
      }
      return;
    }

    if (isSpeakingQuestion && "speechSynthesis" in window) {
      window.speechSynthesis.cancel();
      setIsSpeakingQuestion(false);
    }

    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (SpeechRecognition) {
      try {
        if (recognitionRef.current) {
          try { recognitionRef.current.abort(); } catch {}
        }

        const recognition = new SpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = "en-US";

        recognition.onstart = () => {
          setIsListeningMic(true);
          setError(null);
        };

        recognition.onresult = (event: any) => {
          let fullTranscript = "";
          for (let i = 0; i < event.results.length; i++) {
            fullTranscript += event.results[i][0].transcript + " ";
          }
          const clean = fullTranscript.trim();
          if (clean) {
            setCandidateAnswer(clean);
          }
        };

        recognition.onerror = (e: any) => {
          console.warn("Speech recognition notice (handled by backend faster-whisper):", e.error);
        };

        recognition.onend = () => {};

        recognitionRef.current = recognition;
        recognition.start();
      } catch (err: any) {
        console.warn("Speech start error:", err);
      }
    }
  };

  const stopMicListening = () => {
    if (liveIntervalRef.current) {
      clearInterval(liveIntervalRef.current);
      liveIntervalRef.current = null;
    }

    if (recognitionRef.current) {
      try { recognitionRef.current.stop(); } catch {}
    }

    const mr = mediaRecorderRef.current;
    if (mr && mr.state !== "inactive") {
      mr.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: mr.mimeType || "audio/webm" });
        if (audioBlob.size > 500) {
          try {
            setIsTranscribing(true);
            const transcript = await api.transcribeAudioFile(audioBlob);
            if (transcript && transcript.trim()) {
              setCandidateAnswer(transcript.trim());
            }
          } catch (e: any) {
            console.warn("Backend STT error:", e);
          } finally {
            setIsTranscribing(false);
            if (micStreamRef.current) {
              micStreamRef.current.getTracks().forEach((track) => track.stop());
              micStreamRef.current = null;
            }
          }
        } else {
          if (micStreamRef.current) {
            micStreamRef.current.getTracks().forEach((track) => track.stop());
            micStreamRef.current = null;
          }
        }
      };
      try { mr.stop(); } catch {}
    } else {
      if (micStreamRef.current) {
        micStreamRef.current.getTracks().forEach((track) => track.stop());
        micStreamRef.current = null;
      }
    }
    setIsListeningMic(false);
  };

  const toggleMicListening = () => {
    if (isListeningMic) {
      stopMicListening();
    } else {
      startMicListening();
    }
  };

  const handleQuickVoiceSample = () => {
    if (!currentQuestion) return;
    const comp = currentQuestion.question.competency.toLowerCase();
    let sample = "";
    if (comp.includes("role") || comp.includes("screening")) {
      sample = "I applied for this role because I am passionate about building production AI backend architectures. In my recent work, I built asynchronous REST APIs using FastAPI and PostgreSQL handling 15,000 requests per minute with sub-100ms response times. I also implemented RAG pipelines with Qdrant vector database and Redis semantic caching, which directly aligns with Student Credibility's requirements.";
    } else if (comp.includes("fastapi") || comp.includes("python") || comp.includes("async")) {
      sample = "In Python and FastAPI, I utilize AsyncIO non-blocking event loops, Pydantic v2 schemas for strict serialization, and connection pooling with SQLAlchemy. For instance, I optimized database latency by 45% using indexed foreign keys and connection pooling on Neon PostgreSQL.";
    } else if (comp.includes("rag") || comp.includes("vector") || comp.includes("llm")) {
      sample = "For our RAG pipelines, I used Qdrant Cloud to index document chunks using 384-dimensional dense embeddings. I implemented semantic section chunking with 80-character overlaps and integrated Redis distributed caching to store frequent prompt query embeddings, reducing latency by 40%.";
    } else {
      sample = "In my previous engineering projects, I focused on high-concurrency architecture, robust error handling, automated testing with pytest, and maintaining 99.9% uptime across production Docker containers.";
    }
    setCandidateAnswer(sample);
  };

  const handleAnalyzeDocuments = async () => {
    try {
      setLoading(true);
      setError(null);
      await api.loginDemo();

      let createdJob: Job;
      if (jdInputMode === "upload" && jdFile) {
        createdJob = await api.uploadJobFile(jdFile, jdTitle, jdCompany);
      } else {
        createdJob = await api.createJob(jdTitle, jdText, jdCompany);
      }
      setJob(createdJob);

      let createdResume: Resume;
      if (resumeInputMode === "upload" && resumeFile) {
        createdResume = await api.uploadResumeFile(resumeFile, candidateName);
      } else {
        createdResume = await api.createResume(resumeText, candidateName);
      }
      setResume(createdResume);

      const fit = await api.calculateJobFit(createdJob.id, createdResume.id);
      setJobFit(fit);

      setActiveTab("role");
    } catch (err: any) {
      setError(err.message || "Failed to process documents");
    } finally {
      setLoading(false);
    }
  };

  const handleStartInterview = async () => {
    if (!job || !resume) return;
    try {
      setLoading(true);
      setError(null);

      const session = await api.createInterview(job.id, resume.id, "voice");
      setInterviewId(session.id);

      const firstQ = await api.startInterview(session.id);
      setCurrentQuestion(firstQ);
      setLatestEvaluation(null);
      setCandidateAnswer("");
      setActiveTab("interview");
      speakText(firstQ.question.text);
    } catch (err: any) {
      setError(err.message || "Failed to start interview");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitAnswer = async () => {
    if (!interviewId || !currentQuestion || !candidateAnswer.trim()) return;

    if (isListeningMic && recognitionRef.current) {
      recognitionRef.current.stop();
      setIsListeningMic(false);
    }

    try {
      setLoading(true);
      setError(null);

      const evaluation = await api.submitAnswer(
        interviewId,
        currentQuestion.question_id,
        candidateAnswer,
        45000,
        135
      );
      setLatestEvaluation(evaluation);

      const updatedQ = await api.getCurrentQuestion(interviewId).catch(() => null);
      if (updatedQ && updatedQ.question_id !== currentQuestion.question_id) {
        setTimeout(() => {
          setCurrentQuestion(updatedQ);
          setCandidateAnswer("");
          speakText(updatedQ.question.text);
        }, 1800);
      } else {
        setTimeout(() => {
          handleFinishInterview();
        }, 2000);
      }
    } catch (err: any) {
      setError(err.message || "Failed to submit answer telemetry");
    } finally {
      setLoading(false);
    }
  };

  const handleFinishInterview = async () => {
    if (!interviewId) return;
    try {
      setLoading(true);
      await api.completeInterview(interviewId);
      const rep = await api.getReport(interviewId);
      const plan = await api.getPreparationPlan(interviewId);
      setReport(rep);
      setPrepPlan(plan);
      setActiveTab("report");
      fetchHistory();

      confetti({
        particleCount: 90,
        spread: 80,
        origin: { y: 0.6 },
      });
    } catch (err: any) {
      setError(err.message || "Failed to compile diagnostic log");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-chassis text-ink pb-20">
      {/* Top Industrial Chassis Bar */}
      <header className="bg-chassis border-b border-[#a3b1c6]/40 shadow-card sticky top-0 z-30">
        <div className="max-w-7xl mx-auto px-6 py-4 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-lg bg-[#2d3436] shadow-sharp flex items-center justify-center border border-white/20">
              <Cpu className="w-6 h-6 text-safety" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-mono text-sm px-2 py-0.5 bg-safety text-white rounded font-bold uppercase tracking-wider shadow-sm">
                  CHECKOUT // MOD-01
                </span>
                <span className="font-mono text-xs text-inkMuted uppercase">
                  SYSTEM ONLINE
                </span>
              </div>
              <h1 className="font-mono text-xl md:text-2xl font-bold uppercase tracking-tight text-ink mt-0.5">
                Checkout Console
              </h1>
            </div>
          </div>

          {/* Telemetry LED Status */}
          <div className="hidden lg:flex items-center gap-6 p-2 bg-chassis rounded-md shadow-recessed px-4">
            <LedIndicator status="green" label="DB_CONN: OK" />
            <LedIndicator status="green" label="CACHE: READY" />
            <LedIndicator status="amber" label="VAD: 16KHZ" />
          </div>

          {/* Stage Buttons */}
          <div className="flex items-center gap-2 overflow-x-auto w-full md:w-auto pb-1 sm:pb-0 no-scrollbar shrink-0">
            <nav className="flex items-center gap-1.5 sm:gap-2 overflow-x-auto w-full md:w-auto pb-1 sm:pb-0 no-scrollbar shrink-0">
              <button
                onClick={() => setActiveTab("ingest")}
                className={`font-mono text-xs uppercase px-2.5 sm:px-3 py-1.5 sm:py-2 rounded-md mechanical-transition whitespace-nowrap cursor-pointer ${
                  activeTab === "ingest"
                    ? "bg-[#2d3436] text-white shadow-sharp"
                    : "bg-chassis text-ink shadow-floating hover:text-safety"
                }`}
              >
                01 // INGEST
              </button>
              <button
                onClick={() => setActiveTab("role")}
                disabled={!job}
                className={`font-mono text-xs uppercase px-2.5 sm:px-3 py-1.5 sm:py-2 rounded-md mechanical-transition whitespace-nowrap cursor-pointer disabled:opacity-40 ${
                  activeTab === "role"
                    ? "bg-[#2d3436] text-white shadow-sharp"
                    : "bg-chassis text-ink shadow-floating hover:text-safety"
                }`}
              >
                02 // ROLE_SPEC
              </button>
              <button
                onClick={() => setActiveTab("fit")}
                disabled={!jobFit}
                className={`font-mono text-xs uppercase px-2.5 sm:px-3 py-1.5 sm:py-2 rounded-md mechanical-transition whitespace-nowrap cursor-pointer disabled:opacity-40 ${
                  activeTab === "fit"
                    ? "bg-[#2d3436] text-white shadow-sharp"
                    : "bg-chassis text-ink shadow-floating hover:text-safety"
                }`}
              >
                03 // FIT_SCORE
              </button>
              <button
                onClick={() => setActiveTab("interview")}
                disabled={!currentQuestion}
                className={`font-mono text-xs uppercase px-2.5 sm:px-3 py-1.5 sm:py-2 rounded-md mechanical-transition whitespace-nowrap cursor-pointer disabled:opacity-40 ${
                  activeTab === "interview"
                    ? "bg-safety text-white shadow-safety"
                    : "bg-chassis text-ink shadow-floating hover:text-safety"
                }`}
              >
                04 // SIMULATOR
              </button>
              <button
                onClick={() => setActiveTab("report")}
                disabled={!report}
                className={`font-mono text-xs uppercase px-2.5 sm:px-3 py-1.5 sm:py-2 rounded-md mechanical-transition whitespace-nowrap cursor-pointer disabled:opacity-40 ${
                  activeTab === "report"
                    ? "bg-[#10b981] text-white shadow-sharp"
                    : "bg-chassis text-ink shadow-floating hover:text-safety"
                }`}
              >
                05 // TELEMETRY
              </button>
              <button
                onClick={() => {
                  setActiveTab("history");
                  fetchHistory();
                }}
                className={`font-mono text-xs uppercase px-2.5 sm:px-3 py-1.5 sm:py-2 rounded-md mechanical-transition whitespace-nowrap cursor-pointer flex items-center gap-1.5 ${
                  activeTab === "history"
                    ? "bg-[#8b5cf6] text-white shadow-sharp"
                    : "bg-chassis text-ink shadow-floating hover:text-safety"
                }`}
              >
                <History className="w-3.5 h-3.5" />
                <span>06 // HISTORY</span>
                {historySummary && (
                  <span className={`text-[10px] px-1 py-0.2 rounded font-mono font-bold ${
                    activeTab === "history" ? "bg-white text-[#8b5cf6]" : "bg-[#2d3436] text-white"
                  }`}>
                    {historySummary.total_interviews}
                  </span>
                )}
              </button>
            </nav>

            <button
              type="button"
              onClick={handleResetSession}
              title="Reset telemetry cache"
              className="font-mono text-xs uppercase px-2 py-1.5 rounded-md bg-chassis text-ink shadow-floating hover:text-safety border border-white/40 mechanical-transition cursor-pointer shrink-0 flex items-center gap-1 ml-1"
            >
              <RotateCcw className="w-3 h-3" />
              <span className="hidden sm:inline">RESET</span>
            </button>
          </div>
        </div>
      </header>

      {/* Main Console Viewport */}
      <main className="max-w-7xl mx-auto px-3 sm:px-6 pt-4 sm:pt-8">
        {error && (
          <div className="mb-6 p-4 bg-[#fee2e2] rounded-lg shadow-sharp border border-safety/60 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <AlertOctagon className="w-5 h-5 text-safety" />
              <span className="font-mono text-sm text-safety font-bold uppercase">{error}</span>
            </div>
            <button onClick={() => setError(null)} className="font-mono text-xs font-bold uppercase text-ink">
              DISMISS
            </button>
          </div>
        )}

        {/* TAB 1: INGEST */}
        {activeTab === "ingest" && (
          <div className="space-y-8">
            <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 border-b border-[#a3b1c6]/30 pb-4">
              <div>
                <span className="font-mono text-xs uppercase text-inkMuted">
                  SUBSYSTEM: SPECIFICATION_PARSER
                </span>
                <h2 className="font-mono text-2xl font-bold uppercase tracking-tight text-ink mt-1">
                  Load Target Requirements & Candidate Profile
                </h2>
              </div>
              <div className="flex items-center gap-3">
                <LedIndicator status="green" label="PARSER_READY" />
              </div>
            </div>

            <div className="grid md:grid-cols-2 gap-8">
              {/* Job Panel */}
              <IndustrialCard title="01 // TARGET JOB DESCRIPTION" subtitle="ENTER ROLES & REQUIREMENTS">
                <div className="space-y-4">
                  <div className="flex items-center justify-between pb-2 border-b border-[#a3b1c6]/30">
                    <span className="font-mono text-xs uppercase text-inkMuted">INGESTION_VECTOR:</span>
                    <div className="flex items-center gap-1 bg-[#10141d]/10 p-1 rounded-md">
                      <button
                        type="button"
                        onClick={() => setJdInputMode("upload")}
                        className={`font-mono text-xs px-2.5 py-1 rounded transition-all cursor-pointer ${
                          jdInputMode === "upload"
                            ? "bg-steel text-white font-bold shadow-sm"
                            : "text-inkMuted hover:text-ink font-medium"
                        }`}
                      >
                        <Upload className="w-3 h-3 inline mr-1" /> UPLOAD_FILE
                      </button>
                      <button
                        type="button"
                        onClick={() => setJdInputMode("paste")}
                        className={`font-mono text-xs px-2.5 py-1 rounded transition-all cursor-pointer ${
                          jdInputMode === "paste"
                            ? "bg-safety text-white font-bold shadow-sm"
                            : "text-inkMuted hover:text-ink font-medium"
                        }`}
                      >
                        PASTE_TEXT
                      </button>
                    </div>
                  </div>

                  <IndustrialInput
                    label="Role Title"
                    badge="MANDATORY"
                    value={jdTitle}
                    onChange={(e) => setJdTitle(e.target.value)}
                  />
                  <IndustrialInput
                    label="Target Organization"
                    badge="METADATA"
                    value={jdCompany}
                    onChange={(e) => setJdCompany(e.target.value)}
                  />
                  {jdInputMode === "upload" ? (
                    <div>
                      <span className="font-mono text-xs text-inkMuted uppercase block mb-1.5 font-bold">
                        PAYLOAD_PAYLOAD: FILE (.PDF, .TXT, .MD, .DOCX)
                      </span>
                      <div className="border border-dashed border-[#a3b1c6] rounded-lg p-6 text-center bg-chassis/60 hover:bg-chassis transition-all cursor-pointer relative shadow-sharpInset">
                        <input
                          type="file"
                          accept=".pdf,.txt,.md,.docx,.doc"
                          onChange={(e) => {
                            if (e.target.files && e.target.files[0]) {
                              setJdFile(e.target.files[0]);
                            }
                          }}
                          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                        />
                        <Upload className="w-8 h-8 text-safety mx-auto mb-2 animate-pulse" />
                        {jdFile ? (
                          <div>
                            <p className="font-mono text-sm text-safety font-bold">{jdFile.name}</p>
                            <p className="font-mono text-xs text-inkMuted">{(jdFile.size / 1024).toFixed(1)} KB — BUFFER_MOUNTED</p>
                          </div>
                        ) : (
                          <div>
                            <p className="font-mono text-sm text-ink font-bold">DROP_FILE OR CLICK TO SELECT</p>
                            <p className="font-mono text-xs text-inkMuted">FORMATS: PDF, TXT, MARKDOWN, DOCX</p>
                          </div>
                        )}
                      </div>
                    </div>
                  ) : (
                    <IndustrialTextarea
                      label="Job Description Payload"
                      badge="RAW_TEXT"
                      rows={8}
                      value={jdText}
                      onChange={(e) => setJdText(e.target.value)}
                      className="no-scrollbar"
                    />
                  )}
                </div>
              </IndustrialCard>

              {/* Resume Panel */}
              <IndustrialCard title="02 // CANDIDATE DOSSIER" subtitle="VERIFIABLE CLAIMS & EXPERIENCE">
                <div className="space-y-4">
                  <div className="flex items-center justify-between pb-2 border-b border-[#a3b1c6]/30">
                    <span className="font-mono text-xs uppercase text-inkMuted">INGESTION_VECTOR:</span>
                    <div className="flex items-center gap-1 bg-[#10141d]/10 p-1 rounded-md">
                      <button
                        type="button"
                        onClick={() => setResumeInputMode("upload")}
                        className={`font-mono text-xs px-2.5 py-1 rounded transition-all cursor-pointer ${
                          resumeInputMode === "upload"
                            ? "bg-steel text-white font-bold shadow-sm"
                            : "text-inkMuted hover:text-ink font-medium"
                        }`}
                      >
                        <Upload className="w-3 h-3 inline mr-1" /> UPLOAD_FILE
                      </button>
                      <button
                        type="button"
                        onClick={() => setResumeInputMode("paste")}
                        className={`font-mono text-xs px-2.5 py-1 rounded transition-all cursor-pointer ${
                          resumeInputMode === "paste"
                            ? "bg-steel text-white font-bold shadow-sm"
                            : "text-inkMuted hover:text-ink font-medium"
                        }`}
                      >
                        TEXT_PAYLOAD
                      </button>
                    </div>
                  </div>

                  <IndustrialInput
                    label="Candidate Name"
                    badge="IDENTIFIER"
                    value={candidateName}
                    onChange={(e) => setCandidateName(e.target.value)}
                  />

                  {resumeInputMode === "upload" ? (
                    <div className="space-y-2">
                      <label className="block font-mono text-xs font-bold uppercase tracking-wider text-inkMuted">
                        BINARY DOSSIER SOURCE (PDF / DOCX / TXT)
                      </label>
                      <div className="border-2 border-dashed border-[#a3b1c6] rounded-lg p-6 text-center bg-chassis hover:border-steel transition-all relative">
                        <input
                          type="file"
                          accept=".pdf,.docx,.doc,.txt"
                          onChange={(e) => {
                            if (e.target.files && e.target.files[0]) {
                              setResumeFile(e.target.files[0]);
                            }
                          }}
                          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
                        />
                        <div className="flex flex-col items-center justify-center gap-2 pointer-events-none">
                          {resumeFile ? (
                            <>
                              <FileCheck className="w-10 h-10 text-[#10b981]" />
                              <p className="font-mono text-base font-bold text-ink uppercase">{resumeFile.name}</p>
                              <p className="font-mono text-xs text-inkMuted">
                                {(resumeFile.size / 1024).toFixed(1)} KB • READY FOR B2 &amp; QDRANT CLOUD
                              </p>
                              <span className="font-mono text-xs text-steel underline uppercase font-bold">CLICK OR DRAG TO REPLACE</span>
                            </>
                          ) : (
                            <>
                              <Upload className="w-10 h-10 text-inkMuted" />
                              <p className="font-mono text-sm font-bold uppercase text-ink">
                                DRAG &amp; DROP OR CLICK TO MOUNT FILE
                              </p>
                              <p className="font-mono text-xs text-inkMuted">
                                FORMATS: PDF // WORD (DOCX) // TXT
                              </p>
                              <div className="mt-2 inline-flex items-center gap-1.5 font-mono text-[10px] bg-[#10b981]/15 text-[#047857] px-2.5 py-0.5 rounded border border-[#10b981]/30 font-bold uppercase">
                                <Database className="w-3 h-3 text-[#10b981]" /> Auto-Chunked &amp; Upserted to Qdrant Cloud
                              </div>
                            </>
                          )}
                        </div>
                      </div>
                    </div>
                  ) : (
                    <IndustrialTextarea
                      label="Resume Text Payload"
                      badge="RAW_TEXT"
                      rows={12}
                      value={resumeText}
                      onChange={(e) => setResumeText(e.target.value)}
                    />
                  )}
                </div>
              </IndustrialCard>
            </div>

            <div className="flex justify-center pt-4">
              <IndustrialButton
                size="lg"
                variant="primary"
                onClick={handleAnalyzeDocuments}
                disabled={loading}
              >
                {loading ? (
                  <>
                    <Activity className="w-5 h-5 animate-spin" /> EXECUTING EXTRACTION PIPELINE...
                  </>
                ) : (
                  <>
                    EXECUTE ANALYSIS & COMPUTE JOB FIT <ArrowRight className="w-5 h-5" />
                  </>
                )}
              </IndustrialButton>
            </div>
          </div>
        )}

        {/* TAB 2: ROLE SPEC */}
        {activeTab === "role" && job && (
          <div className="space-y-6">
            <div className="flex flex-wrap items-center justify-between gap-4 border-b border-[#a3b1c6]/30 pb-4">
              <div>
                <span className="font-mono text-xs uppercase text-inkMuted">
                  SUBSYSTEM: ROLE_DECOMPOSITION
                </span>
                <h2 className="font-mono text-2xl font-bold uppercase tracking-tight text-ink mt-1">
                  {job.analysis?.role_title || job.title}
                </h2>
                <p className="font-mono text-xs text-inkMuted mt-0.5">
                  CALIBRATED SENIORITY: <strong className="text-safety uppercase">{job.analysis?.seniority}</strong>
                </p>
              </div>

              <IndustrialButton size="md" variant="secondary" onClick={() => setActiveTab("fit")}>
                PROCEED TO FIT DIAGNOSTICS <ArrowRight className="w-4 h-4" />
              </IndustrialButton>
            </div>

            <div className="grid md:grid-cols-2 gap-6">
              {/* Required Skills */}
              <IndustrialCard title="COMPETENCY_REGISTER: REQUIRED" subtitle="CORE TECHNICAL PREREQUISITES">
                <div className="flex flex-wrap gap-2 mb-6">
                  {job.analysis?.required_skills.map((skill, i) => (
                    <span
                      key={i}
                      className="font-mono text-xs font-bold px-3 py-1.5 bg-chassis text-ink rounded shadow-floating border border-white/60"
                    >
                      {skill}
                    </span>
                  ))}
                </div>

                <span className="font-mono text-xs font-bold uppercase text-inkMuted block mb-2">
                  SECONDARY / PREFERRED
                </span>
                <div className="flex flex-wrap gap-2">
                  {job.analysis?.preferred_skills.map((skill, i) => (
                    <span
                      key={i}
                      className="font-mono text-xs px-2.5 py-1 bg-recessed text-inkMuted rounded shadow-recessed"
                    >
                      {skill}
                    </span>
                  ))}
                </div>
              </IndustrialCard>

              {/* Technical Profile */}
              <IndustrialCard title="ARCHITECTURE & BEHAVIOR" subtitle="OPERATIONAL ATTRIBUTES">
                <div className="space-y-4">
                  <div className="p-3 bg-chassis rounded shadow-recessed">
                    <span className="font-mono text-[10px] text-inkMuted uppercase block">
                      TECHNICAL DOMAINS
                    </span>
                    <p className="font-mono text-xs text-ink mt-1 font-bold">
                      {job.analysis?.technical_competencies.join(" // ")}
                    </p>
                  </div>

                  <div className="p-3 bg-chassis rounded shadow-recessed">
                    <span className="font-mono text-[10px] text-inkMuted uppercase block">
                      BEHAVIOURAL BENCHMARKS
                    </span>
                    <p className="font-mono text-xs text-ink mt-1 font-bold">
                      {job.analysis?.behavioral_competencies.join(" // ")}
                    </p>
                  </div>

                  <div className="p-3 bg-chassis rounded shadow-recessed">
                    <span className="font-mono text-[10px] text-inkMuted uppercase block">
                      EXPERIENCE EXPECTATIONS
                    </span>
                    <p className="font-mono text-xs text-ink mt-1 italic">
                      {job.analysis?.experience_expectations}
                    </p>
                  </div>
                </div>
              </IndustrialCard>

              {/* Responsibilities */}
              <IndustrialCard title="OPERATIONAL RESPONSIBILITIES" subtitle="DEPLOYMENT SCOPE" className="md:col-span-2">
                <ul className="space-y-2 font-mono text-xs text-ink">
                  {job.analysis?.responsibilities.map((r, i) => (
                    <li key={i} className="flex items-start gap-2">
                      <span className="text-safety font-bold">[{i + 1}]</span>
                      <span>{r}</span>
                    </li>
                  ))}
                </ul>
              </IndustrialCard>
            </div>
          </div>
        )}

        {/* TAB 3: FIT SCORE */}
        {activeTab === "fit" && jobFit && (
          <div className="space-y-6">
            <div className="flex flex-wrap items-center justify-between gap-4 border-b border-[#a3b1c6]/30 pb-4">
              <div>
                <span className="font-mono text-xs uppercase text-inkMuted">
                  SUBSYSTEM: HYBRID_FIT_ENGINE
                </span>
                <h2 className="font-mono text-2xl font-bold uppercase tracking-tight text-ink mt-1">
                  Explainable Fit Diagnostic
                </h2>
              </div>

              <IndustrialButton size="lg" variant="primary" onClick={handleStartInterview}>
                INITIATE SIMULATOR ROUNDS <Play className="w-4 h-4 fill-white" />
              </IndustrialButton>
            </div>

            {/* Score HUD */}
            <div className="p-6 bg-chassis rounded-xl shadow-floating border border-white/60 flex flex-col md:flex-row items-center justify-between gap-6">
              <div className="text-center md:text-left">
                <span className="font-mono text-xs text-inkMuted uppercase block">
                  CUMULATIVE CALIBRATION SCORE
                </span>
                <div className="font-mono text-5xl md:text-6xl font-bold text-ink mt-1">
                  {jobFit.overall_score}%
                </div>
                <span className="font-mono text-xs text-safety font-bold uppercase">
                  CLASSIFICATION: {jobFit.classification}
                </span>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 flex-1 max-w-2xl">
                {Object.entries(jobFit.dimensions).map(([k, v]) => (
                  <div key={k} className="p-3 bg-chassis rounded shadow-recessed">
                    <span className="font-mono text-[10px] text-inkMuted uppercase block truncate">
                      {k.replace("_", " ")}
                    </span>
                    <span className="font-mono text-lg font-bold text-ink">{v}%</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Evidence Tables */}
            <div className="grid md:grid-cols-2 gap-6">
              {/* Verified Matches */}
              <IndustrialCard title="VERIFIED COMPETENCIES" subtitle="EVIDENCE-BACKED OVERLAP">
                <div className="space-y-3">
                  {jobFit.matches.map((m, i) => (
                    <div key={i} className="p-3 bg-chassis rounded shadow-recessed">
                      <div className="flex items-center justify-between">
                        <span className="font-mono text-xs font-bold text-ink">{m.skill}</span>
                        <span className="font-mono text-[10px] bg-[#10b981] text-white px-2 py-0.5 rounded">
                          VERIFIED
                        </span>
                      </div>
                      <p className="font-mono text-[11px] text-inkMuted mt-1">
                        <strong>JD:</strong> {m.jd_evidence}
                      </p>
                      <p className="font-mono text-[11px] text-ink mt-0.5">
                        <strong>RESUME:</strong> {m.resume_evidence}
                      </p>
                    </div>
                  ))}
                </div>
              </IndustrialCard>

              {/* Partial & Missing */}
              <IndustrialCard title="DEFICITS & PARTIAL MATCHES" subtitle="CALIBRATION TARGETS">
                <div className="space-y-3">
                  {jobFit.partial_matches.map((p, i) => (
                    <div key={i} className="p-3 bg-chassis rounded shadow-recessed border-l-2 border-safety">
                      <div className="flex items-center justify-between">
                        <span className="font-mono text-xs font-bold text-ink">{p.skill}</span>
                        <span className="font-mono text-[10px] bg-[#f59e0b] text-white px-2 py-0.5 rounded">
                          PARTIAL
                        </span>
                      </div>
                      <p className="font-mono text-[11px] text-safety mt-1 font-bold">
                        GAP: {p.gap}
                      </p>
                    </div>
                  ))}

                  {jobFit.missing_skills.map((m, i) => (
                    <div key={i} className="p-3 bg-chassis rounded shadow-recessed border-l-2 border-[#2d3436]">
                      <div className="flex items-center justify-between">
                        <span className="font-mono text-xs font-bold text-ink">{m.skill}</span>
                        <span className="font-mono text-[10px] bg-safety text-white px-2 py-0.5 rounded">
                          MISSING
                        </span>
                      </div>
                      <p className="font-mono text-[11px] text-inkMuted mt-1">
                        Skill not detected in resume artifacts.
                      </p>
                    </div>
                  ))}
                </div>
              </IndustrialCard>
            </div>

            {/* Qdrant Vector Telemetry & Chunk Ingestion Console (At the end of the page) */}
            <div className="p-5 bg-chassis rounded-xl shadow-floating border border-white/60 space-y-4">
              <div className="flex flex-wrap items-center justify-between gap-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-chassis shadow-recessed flex items-center justify-center text-[#10b981] border border-white/20">
                    <Database className="w-5 h-5" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-sm font-bold uppercase tracking-wider text-ink">
                        QDRANT CLOUD VECTOR TELEMETRY
                      </span>
                      <span className="inline-flex items-center gap-1 font-mono text-[10px] bg-[#10b981]/15 text-[#047857] px-2 py-0.5 rounded border border-[#10b981]/30 font-bold uppercase">
                        <span className="w-1.5 h-1.5 rounded-full bg-[#10b981] animate-pulse"></span>
                        ONLINE // EMBEDDED
                      </span>
                    </div>
                    <span className="font-mono text-xs text-inkMuted block">
                      COLLECTIONS: <code className="bg-chassis px-1 py-0.5 rounded shadow-recessed text-ink">resume_chunks</code> &amp; <code className="bg-chassis px-1 py-0.5 rounded shadow-recessed text-ink">resume_claims</code> • 384-DIMENSIONAL EMBEDDINGS
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  {resume?.file_url && (
                    <div className="hidden sm:flex items-center gap-1.5 bg-chassis px-2.5 py-1 rounded shadow-recessed font-mono text-[11px] text-inkMuted">
                      <HardDrive className="w-3.5 h-3.5 text-safety" />
                      <span className="truncate max-w-[200px]">{resume.file_url}</span>
                    </div>
                  )}
                  <button
                    type="button"
                    onClick={() => setShowChunksDrawer(!showChunksDrawer)}
                    className="flex items-center gap-1.5 font-mono text-xs font-bold uppercase px-3 py-1.5 rounded-lg bg-steel text-white shadow-raised active:shadow-pressed transition-all cursor-pointer"
                  >
                    <Layers className="w-3.5 h-3.5 text-white" />
                    <span>
                      {showChunksDrawer ? "COLLAPSE_CHUNKS" : `INSPECT_CHUNKS (${resume?.chunks?.length || resume?.chunks_indexed || 3})`}
                    </span>
                    {showChunksDrawer ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                  </button>
                </div>
              </div>

              {/* Collapsible Chunk Viewer */}
              {showChunksDrawer && (
                <div className="pt-3 border-t border-[#a3b1c6]/30 space-y-3">
                  <div className="flex flex-wrap items-center justify-between font-mono text-[11px] text-inkMuted">
                    <span>SEMANTIC SEGMENTATION INGESTED INTO QDRANT CLOUD:</span>
                    <span className="bg-chassis px-2 py-0.5 rounded shadow-recessed text-steel font-bold">
                      MODEL: sentence-transformers (384 DIMS, COSINE)
                    </span>
                  </div>

                  <div className="grid md:grid-cols-2 gap-3 max-h-96 overflow-y-auto pr-1">
                    {(resume?.chunks && resume.chunks.length > 0 ? resume.chunks : [
                      { chunk_index: 0, section: "summary", text: resume?.candidate_name ? `Profile dossier for ${resume.candidate_name}: software engineering background.` : "Summary of candidate technical experience and background.", char_count: 140 },
                      { chunk_index: 1, section: "experience", text: "Production backend engineering with FastAPI, Qdrant vector database, Redis caching, and PostgreSQL database pipelines.", char_count: 220 },
                      { chunk_index: 2, section: "skills", text: "Core technical proficiencies: Python, FastAPI, AsyncIO, PyTorch, RAG architectures, Docker, Backblaze B2, REST APIs.", char_count: 180 }
                    ]).map((ch, idx) => (
                      <div key={idx} className="p-3 bg-chassis rounded-lg shadow-recessed border border-[#a3b1c6]/20">
                        <div className="flex items-center justify-between gap-2 mb-1.5">
                          <span className="font-mono text-xs font-bold text-ink uppercase">
                            CHUNK #{ch.chunk_index + 1} // {ch.section}
                          </span>
                          <span className="font-mono text-[10px] bg-chassis px-1.5 py-0.5 rounded shadow-raised text-inkMuted">
                            {ch.char_count} CHARS
                          </span>
                        </div>
                        <p className="font-mono text-[11px] text-inkMuted bg-chassis/60 p-2 rounded line-clamp-3">
                          {ch.text}
                        </p>
                        <div className="mt-2 flex items-center justify-between font-mono text-[10px] text-inkMuted">
                          <span>POINT_ID: 0x{((idx + 1) * 314159).toString(16).slice(0, 6)}</span>
                          <span className="text-[#10b981] font-bold">QDRANT_UPSERTED</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* TAB 4: SIMULATOR */}
        {activeTab === "interview" && currentQuestion && (
          <div className="space-y-6">
            {/* Header Stage HUD */}
            <div className="p-4 bg-chassis rounded-lg shadow-card border border-white/60 flex flex-wrap items-center justify-between gap-4">
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 rounded bg-[#2d3436] text-white font-mono text-base font-bold flex items-center justify-center shadow-sharp">
                  Q{currentQuestion.sequence}
                </div>
                <div>
                  <span className="font-mono text-[10px] uppercase text-inkMuted">
                    SIMULATION PHASE
                  </span>
                  <div className="font-mono text-base font-bold uppercase text-safety">
                    {currentQuestion.level.replace("_", " ")} ROUND
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-6 font-mono text-xs text-ink">
                <span>DIFFICULTY: <strong>{currentQuestion.question.difficulty} / 10</strong></span>
                <span>PROGRESS: <strong>{currentQuestion.state.progress_percent}%</strong></span>
              </div>

              <div className="flex items-center gap-3">
                <button
                  onClick={() => setTtsEnabled(!ttsEnabled)}
                  className="p-2 rounded bg-chassis shadow-floating text-ink hover:text-safety"
                  title="Toggle Speech Audio"
                >
                  {ttsEnabled ? <Volume2 className="w-4 h-4" /> : <VolumeX className="w-4 h-4 text-safety" />}
                </button>
                <IndustrialButton size="sm" variant="dark" onClick={handleFinishInterview}>
                  ABORT & COMPILE
                </IndustrialButton>
              </div>
            </div>

            <div className="flex flex-col md:grid md:grid-cols-3 gap-6 items-start">
              {/* 1. CRT Terminal Screen for Question (Order-1 on mobile) */}
              <div className="order-1 md:col-start-2 md:col-span-2 md:row-start-1 w-full">
                <div className="p-6 bg-[#1e272e] rounded-lg shadow-recessed border border-[#1e272e] relative overflow-hidden">
                  <div className="flex items-center justify-between mb-3 border-b border-[#34495e] pb-2">
                    <span className="font-mono text-xs text-[#2ed573] font-bold uppercase tracking-wider flex items-center gap-2">
                      <Terminal className="w-4 h-4" /> INTERVIEWER_QUERY_CHANNEL
                    </span>
                    <button
                      onClick={() => speakText(currentQuestion.question.text)}
                      className="font-mono text-xs text-[#a4b0be] hover:text-white flex items-center gap-1 underline"
                    >
                      <Volume2 className="w-3.5 h-3.5" /> RE-SYNTHESIZE
                    </button>
                  </div>

                  <p className="font-mono text-base leading-relaxed text-[#ecf0f1]">
                    {currentQuestion.question.text}
                  </p>

                  <div className="mt-4 pt-2 border-t border-[#34495e] flex items-center justify-between font-mono text-[10px] text-[#7f8c8d] uppercase">
                    <span>TARGET_COMPETENCY: {currentQuestion.question.competency}</span>
                    <span>TYPE: {currentQuestion.question.type}</span>
                  </div>

                  <div className="absolute inset-0 crt-scanlines pointer-events-none" />
                </div>
              </div>

              {/* 2. Optical Sensor & Instruments (Order-2 on mobile) */}
              <div className="order-2 md:col-start-1 md:col-span-1 md:row-start-1 md:row-span-2 space-y-6 w-full">
                <IndustrialMonitor />
                {/* Audio Wave Spectrum (Hidden on mobile view, visible only on desktop) */}
                <div className="hidden md:block">
                  <OscilloscopeWave
                    isListening={isListeningMic}
                    isSpeaking={isSpeakingQuestion}
                  />
                </div>
              </div>

              {/* 3. Candidate Transmission Slot (Order-3 on mobile) */}
              <div className="order-3 md:col-start-2 md:col-span-2 md:row-start-2 space-y-6 w-full">
                <IndustrialCard title="03 // CANDIDATE TRANSMISSION" subtitle="AUDIO STT OR DIRECT DATA ENTRY">
                  {isListeningMic && (
                    <div className="flex items-center gap-2 p-2.5 bg-[#2ed573]/15 border border-[#2ed573]/40 rounded-md text-ink font-mono text-xs animate-pulse mb-3">
                      <Mic className="w-4 h-4 text-safety animate-bounce" />
                      <span><strong>AUDIO RECEIVER ENGAGED:</strong> Audio stream active. Transcribed phonemes materialize below in real-time.</span>
                    </div>
                  )}

                  {isTranscribing && (
                    <div className="flex items-center gap-2 p-2.5 bg-[#f59e0b]/15 border border-[#f59e0b]/40 rounded-md text-ink font-mono text-xs animate-pulse mb-3">
                      <Sparkles className="w-4 h-4 text-[#f59e0b] animate-spin" />
                      <span><strong>PROCESSING NEURAL STT:</strong> Faster-Whisper transcribing audio recording...</span>
                    </div>
                  )}

                  <IndustrialTextarea
                    rows={6}
                    value={candidateAnswer}
                    onChange={(e) => setCandidateAnswer(e.target.value)}
                    placeholder="ENGAGE 'AUDIO RECEIVER' OR TYPE CANDIDATE RESPONSE..."
                  />

                  <div className="flex flex-wrap items-center justify-between gap-3 mt-4 pt-3 border-t border-[#a3b1c6]/30">
                    <div className="flex flex-wrap items-center gap-2">
                      <IndustrialButton
                        variant={isListeningMic ? "primary" : "secondary"}
                        onClick={toggleMicListening}
                      >
                        <Mic className={`w-4 h-4 ${isListeningMic ? "animate-pulse text-safety" : ""}`} />
                        {isListeningMic ? "HALT AUDIO CAPTURE" : "ENGAGE AUDIO RECEIVER"}
                      </IndustrialButton>

                      <IndustrialButton
                        variant="secondary"
                        size="sm"
                        onClick={handleQuickVoiceSample}
                        title="Auto-fill candidate voice answer calibrated to this competency"
                      >
                        <Sparkles className="w-3.5 h-3.5 text-safety" /> AUTO-SIMULATE
                      </IndustrialButton>
                    </div>

                    <IndustrialButton
                      variant="primary"
                      onClick={handleSubmitAnswer}
                      disabled={loading || !candidateAnswer.trim()}
                    >
                      {loading ? "EVALUATING TELEMETRY..." : "TRANSMIT ANSWER & ADVANCE"}
                    </IndustrialButton>
                  </div>
                </IndustrialCard>

                {/* Real-time telemetry feedback */}
                {latestEvaluation && (
                  <div className="p-4 bg-chassis rounded-lg shadow-card border border-white/60">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-mono text-xs font-bold uppercase text-ink">
                        EVALUATION TELEMETRY: {latestEvaluation.assessment}
                      </span>
                      <span className="font-mono text-base font-bold text-safety">
                        {latestEvaluation.overall_score} / 10
                      </span>
                    </div>
                    <p className="font-mono text-xs text-inkMuted">
                      <strong>STRENGTH:</strong> {latestEvaluation.strengths[0] || "Valid technical baseline."}
                    </p>
                    <p className="font-mono text-xs text-safety mt-1 font-bold">
                      <strong>PROBE_VECTOR:</strong> {latestEvaluation.follow_up_reason}
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* TAB 5: REPORT */}
        {activeTab === "report" && report && (
          <div className="space-y-8">
            <div className="border-b border-[#a3b1c6]/30 pb-4 text-center md:text-left flex flex-col md:flex-row justify-between items-center gap-4">
              <div>
                <span className="font-mono text-xs uppercase text-inkMuted">
                  TELEMETRY ARCHIVE: PERFORMANCE_DOSSIER
                </span>
                <h2 className="font-mono text-3xl font-bold uppercase tracking-tight text-ink mt-1">
                  Final Performance Calibration Report
                </h2>
              </div>

              <IndustrialButton size="md" variant="secondary" onClick={() => setActiveTab("ingest")}>
                <RotateCcw className="w-4 h-4" /> RESTART SESSION
              </IndustrialButton>
            </div>

            {/* Overall Score Plaque */}
            <div className="p-8 bg-chassis rounded-xl shadow-floating border border-white/60 flex flex-col md:flex-row items-center justify-around gap-6 text-center md:text-left">
              <div>
                <span className="font-mono text-xs text-inkMuted uppercase block">
                  AGGREGATED READINESS RATING
                </span>
                <div className="font-mono text-6xl font-bold text-ink mt-1">
                  {report.overall_score}%
                </div>
              </div>

              <div className="p-4 bg-chassis rounded-lg shadow-recessed border border-[#a3b1c6]/40 text-center">
                <span className="font-mono text-[10px] text-inkMuted uppercase block">
                  CLASSIFICATION SEAL
                </span>
                <div className="font-mono text-xl font-bold text-safety mt-1 uppercase tracking-wider">
                  [{report.readiness.classification}]
                </div>
              </div>
            </div>

            {/* Rubrics */}
            <div>
              <span className="font-mono text-xs uppercase text-inkMuted block mb-3">
                COMPETENCY MATRIX CALIBRATION
              </span>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                {[
                  { label: "ROLE_FIT", val: report.role_fit },
                  { label: "TECH_KNOWLEDGE", val: report.technical_knowledge },
                  { label: "PROBLEM_SOLVING", val: report.problem_solving },
                  { label: "COMMUNICATION", val: report.communication },
                  { label: "CONFIDENCE", val: report.confidence },
                  { label: "DEPTH_UNDERSTANDING", val: report.depth },
                  { label: "BEHAVIOURAL_FIT", val: report.behavioral_fit },
                  { label: "MEAN_SCORE", val: report.overall_score },
                ].map((item, i) => (
                  <div key={i} className="p-4 bg-chassis rounded-lg shadow-card border border-white/40">
                    <span className="font-mono text-[10px] text-inkMuted uppercase block">{item.label}</span>
                    <span className="font-mono text-2xl font-bold text-ink mt-1 block">{item.val}%</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Strengths & Weaknesses */}
            <div className="grid md:grid-cols-2 gap-6">
              <IndustrialCard title="DEMONSTRATED CAPABILITIES" subtitle="VERIFIED STRENGTHS">
                <ul className="space-y-2 font-mono text-xs text-ink">
                  {report.strengths.map((s, i) => (
                    <li key={i} className="flex items-start gap-2">
                      <span className="text-[#10b981] font-bold">[+]</span>
                      <span>{s}</span>
                    </li>
                  ))}
                </ul>
              </IndustrialCard>

              <IndustrialCard title="IDENTIFIED VULNERABILITIES" subtitle="AREAS REQUIRING CALIBRATION">
                <ul className="space-y-2 font-mono text-xs text-ink">
                  {report.weaknesses.map((w, i) => (
                    <li key={i} className="flex items-start gap-2">
                      <span className="text-safety font-bold">[-]</span>
                      <span>{w}</span>
                    </li>
                  ))}
                </ul>
              </IndustrialCard>
            </div>

            {/* Preparation Modules */}
            {prepPlan && (
              <div>
                <span className="font-mono text-xs uppercase text-inkMuted block mb-3">
                  PRIORITIZED PREPARATION MODULES
                </span>
                <div className="grid md:grid-cols-3 gap-6">
                  {prepPlan.items.map((item, i) => (
                    <IndustrialCard key={i} title={item.topic} subtitle={`PRIORITY: ${item.priority.toUpperCase()}`}>
                      <p className="font-mono text-[11px] text-safety mb-3 font-bold">
                        TRIGGER: {item.reason}
                      </p>
                      <ul className="space-y-1.5 font-mono text-[11px] text-ink">
                        {item.action_items.map((act, j) => (
                          <li key={j} className="flex items-start gap-1.5">
                            <span className="text-inkMuted">»</span>
                            <span>{act}</span>
                          </li>
                        ))}
                      </ul>
                    </IndustrialCard>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* TAB 6: HISTORY & TELEMETRY ARCHIVE */}
        {activeTab === "history" && (
          <div className="space-y-8">
            <div className="border-b border-[#a3b1c6]/40 pb-4">
              <span className="font-mono text-xs uppercase text-safety block mb-1">
                MODULE 06 // HISTORICAL TELEMETRY LOGS
              </span>
              <h2 className="font-mono text-2xl md:text-3xl font-bold uppercase tracking-tight text-ink">
                Interview Performance Archive
              </h2>
              <p className="font-mono text-xs text-inkMuted mt-1">
                Persistent audit of all past simulation rounds — monitor readiness trends and competency calibrations.
              </p>
            </div>

            {/* Metric Summary Grid */}
            {historySummary && (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <IndustrialCard title="TOTAL SIMULATIONS" subtitle="LOGGED RUNS">
                  <span className="font-mono text-3xl font-bold text-ink block mt-1">
                    {historySummary.total_interviews}
                  </span>
                  <span className="font-mono text-[10px] text-inkMuted uppercase">AUDIT TRAIL ACTIVE</span>
                </IndustrialCard>

                <IndustrialCard title="GOOD ATTEMPTS" subtitle="READY / STRONG">
                  <div className="flex items-center gap-2 mt-1">
                    <ThumbsUp className="w-5 h-5 text-[#10b981]" />
                    <span className="font-mono text-3xl font-bold text-[#10b981]">
                      {historySummary.good_interviews_count}
                    </span>
                  </div>
                  <span className="font-mono text-[10px] text-[#10b981] uppercase font-bold">≥ 70% CALIBRATION</span>
                </IndustrialCard>

                <IndustrialCard title="NEEDS WORK" subtitle="GAPS DETECTED">
                  <div className="flex items-center gap-2 mt-1">
                    <ThumbsDown className="w-5 h-5 text-safety" />
                    <span className="font-mono text-3xl font-bold text-safety">
                      {historySummary.bad_interviews_count}
                    </span>
                  </div>
                  <span className="font-mono text-[10px] text-safety uppercase font-bold">&lt; 70% CALIBRATION</span>
                </IndustrialCard>

                <IndustrialCard title="MEAN SCORE" subtitle="OVERALL AVERAGE">
                  <span className="font-mono text-3xl font-bold text-ink block mt-1">
                    {historySummary.average_score}%
                  </span>
                  <span className="font-mono text-[10px] text-inkMuted uppercase">NORMALIZED METRIC</span>
                </IndustrialCard>
              </div>
            )}

            {/* Filters and Refresh */}
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="flex flex-wrap items-center gap-2">
                <button
                  onClick={() => setHistoryFilter("all")}
                  className={`font-mono text-xs uppercase px-3 py-1.5 rounded-md mechanical-transition cursor-pointer ${
                    historyFilter === "all"
                      ? "bg-[#2d3436] text-white shadow-sharp"
                      : "bg-chassis text-ink shadow-floating hover:text-safety"
                  }`}
                >
                  ALL SESSIONS ({historySummary?.total_interviews || 0})
                </button>
                <button
                  onClick={() => setHistoryFilter("good")}
                  className={`font-mono text-xs uppercase px-3 py-1.5 rounded-md mechanical-transition cursor-pointer flex items-center gap-1.5 ${
                    historyFilter === "good"
                      ? "bg-[#10b981] text-white shadow-sharp"
                      : "bg-chassis text-[#10b981] shadow-floating hover:text-ink"
                  }`}
                >
                  <ThumbsUp className="w-3.5 h-3.5" />
                  GOOD ({historySummary?.good_interviews_count || 0})
                </button>
                <button
                  onClick={() => setHistoryFilter("bad")}
                  className={`font-mono text-xs uppercase px-3 py-1.5 rounded-md mechanical-transition cursor-pointer flex items-center gap-1.5 ${
                    historyFilter === "bad"
                      ? "bg-safety text-white shadow-safety"
                      : "bg-chassis text-safety shadow-floating hover:text-ink"
                  }`}
                >
                  <ThumbsDown className="w-3.5 h-3.5" />
                  NEEDS WORK ({historySummary?.bad_interviews_count || 0})
                </button>
              </div>

              <button
                onClick={fetchHistory}
                disabled={loadingHistory}
                className="font-mono text-xs uppercase px-3 py-1.5 rounded-md bg-chassis text-ink shadow-floating hover:text-safety border border-white/40 mechanical-transition cursor-pointer flex items-center gap-1.5"
              >
                <RotateCcw className={`w-3 h-3 ${loadingHistory ? "animate-spin" : ""}`} />
                <span>{loadingHistory ? "QUERYING DB..." : "POLL ARCHIVE"}</span>
              </button>
            </div>

            {/* Past attempts list */}
            <div className="space-y-4">
              {(!historySummary || historySummary.history.length === 0) ? (
                <IndustrialCard title="NO SIMULATION LOGS FOUND" subtitle="STATUS: IDLE">
                  <p className="font-mono text-xs text-inkMuted mb-4">
                    No completed interviews detected in database. Complete a simulator run to generate telemetry history.
                  </p>
                  <IndustrialButton variant="primary" onClick={() => setActiveTab("ingest")}>
                    INITIALIZE NEW INTERVIEW
                  </IndustrialButton>
                </IndustrialCard>
              ) : (
                historySummary.history
                  .filter((item) => {
                    if (historyFilter === "good") return item.is_good === true;
                    if (historyFilter === "bad") return item.is_good === false;
                    return true;
                  })
                  .map((item) => (
                    <IndustrialCard
                      key={item.interview_id}
                      title={item.job_title}
                      subtitle={`${item.company_name.toUpperCase()} // ${item.status}`}
                    >
                      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 pb-3 border-b border-white/40">
                        <div>
                          <div className="flex flex-wrap items-center gap-2">
                            <span className="font-mono text-xs text-inkMuted">
                              CANDIDATE: <strong>{item.candidate_name}</strong>
                            </span>
                            <span className="font-mono text-xs text-inkMuted">•</span>
                            <span className="font-mono text-xs text-inkMuted">
                              {new Date(item.created_at).toLocaleDateString()} {new Date(item.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                            </span>
                            <span className="font-mono text-xs text-inkMuted">•</span>
                            <span className="font-mono text-xs text-inkMuted">
                              {item.answered_count} / {item.questions_count || 9} ANSWERS
                            </span>
                          </div>
                        </div>

                        <div className="flex items-center gap-3 shrink-0">
                          {item.overall_score !== null && (
                            <div className="text-right">
                              <span className="font-mono text-[10px] text-inkMuted uppercase block">SCORE</span>
                              <span className="font-mono text-2xl font-bold text-ink">
                                {item.overall_score}%
                              </span>
                            </div>
                          )}

                          {item.is_good === true ? (
                            <span className="font-mono text-xs font-bold px-2.5 py-1 rounded bg-[#10b981] text-white shadow-sharp uppercase flex items-center gap-1">
                              <ThumbsUp className="w-3 h-3" /> READY
                            </span>
                          ) : item.is_good === false ? (
                            <span className="font-mono text-xs font-bold px-2.5 py-1 rounded bg-safety text-white shadow-safety uppercase flex items-center gap-1">
                              <ThumbsDown className="w-3 h-3" /> GAPS
                            </span>
                          ) : (
                            <span className="font-mono text-xs font-bold px-2.5 py-1 rounded bg-[#2d3436] text-white uppercase">
                              IN PROGRESS
                            </span>
                          )}
                        </div>
                      </div>

                      {(item.top_strength || item.top_weakness) && (
                        <div className="grid sm:grid-cols-2 gap-2 mt-3 pt-2 font-mono text-xs">
                          {item.top_strength && (
                            <div className="p-2 bg-chassis rounded border border-[#10b981]/30">
                              <strong className="text-[#10b981]">[+] STRENGTH: </strong>
                              <span className="text-ink">{item.top_strength}</span>
                            </div>
                          )}
                          {item.top_weakness && (
                            <div className="p-2 bg-chassis rounded border border-safety/30">
                              <strong className="text-safety">[-] VULNERABILITY: </strong>
                              <span className="text-ink">{item.top_weakness}</span>
                            </div>
                          )}
                        </div>
                      )}

                      <div className="flex justify-end gap-2 mt-3 pt-3 border-t border-white/40">
                        {item.status === "COMPLETED" || item.overall_score !== null ? (
                          <IndustrialButton
                            variant="primary"
                            size="sm"
                            onClick={() => handleViewPastReport(item.interview_id)}
                          >
                            <span className="flex items-center gap-1.5">
                              LOAD DIAGNOSTIC TELEMETRY <ArrowRight className="w-3.5 h-3.5" />
                            </span>
                          </IndustrialButton>
                        ) : (
                          <IndustrialButton
                            variant="secondary"
                            size="sm"
                            onClick={() => handleResumeInterview(item.interview_id)}
                          >
                            <span className="flex items-center gap-1.5">
                              RESUME SESSION <Play className="w-3.5 h-3.5" />
                            </span>
                          </IndustrialButton>
                        )}
                      </div>
                    </IndustrialCard>
                  ))
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
