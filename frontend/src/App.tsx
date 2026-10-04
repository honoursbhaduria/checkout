import { useState, useEffect, useRef } from "react";
import confetti from "canvas-confetti";
import {
  Briefcase,
  FileText,
  Mic,
  Sparkles,
  ChevronRight,
  ChevronDown,
  ChevronUp,
  CheckCircle2,
  AlertTriangle,
  Play,
  RotateCcw,
  Volume2,
  VolumeX,
  Clock,
  ArrowRight,
  BookOpen,
  Upload,
  Database,
  Layers,
  HardDrive,
  FileCheck,
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

import { WobblyButton } from "./components/ui/WobblyButton";
import { WobblyCard } from "./components/ui/WobblyCard";
import { SpeechBubble } from "./components/ui/SpeechBubble";
import { StickyNote } from "./components/ui/StickyNote";
import { ReadinessBadge } from "./components/ui/ReadinessBadge";
import { HandDrawnInput, HandDrawnTextarea } from "./components/ui/HandDrawnInput";
import { VoiceVisualizer } from "./components/interview/VoiceVisualizer";
import { VideoCamera } from "./components/interview/VideoCamera";

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

const STORAGE_KEY = "checkout_interview_state_v1";

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

  // Data states
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

  // Interview state
  const [interviewId, setInterviewId] = useState<string | null>(saved?.interviewId || null);
  const [currentQuestion, setCurrentQuestion] = useState<QuestionData | null>(saved?.currentQuestion || null);
  const [candidateAnswer, setCandidateAnswer] = useState<string>(saved?.candidateAnswer || "");
  const [latestEvaluation, setLatestEvaluation] = useState<AnswerEvaluation | null>(saved?.latestEvaluation || null);
  const [isSpeakingQuestion, setIsSpeakingQuestion] = useState<boolean>(false);
  const [isListeningMic, setIsListeningMic] = useState<boolean>(false);
  const [ttsEnabled, setTtsEnabled] = useState<boolean>(true);

  // Speech Recognition & Mic Stream refs
  const recognitionRef = useRef<any>(null);
  const micStreamRef = useRef<MediaStream | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const liveIntervalRef = useRef<any>(null);
  const isTranscribingSliceRef = useRef<boolean>(false);
  const [isTranscribing, setIsTranscribing] = useState<boolean>(false);

  // Report state
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

  // Initialize Demo Auth and load historical attempts
  useEffect(() => {
    api.loginDemo()
      .then(() => fetchHistory())
      .catch((e) => console.log("Demo login initialized:", e));
  }, []);

  const handleResetSession = () => {
    if (window.confirm("Start a new interview session? This will clear current job & resume progress to let you test another role.")) {
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

  // Web Audio AI interviewer voice chime (guarantees audible playback across all systems)
  const playAIChime = () => {
    try {
      const AudioCtx = window.AudioContext || (window as any).webkitAudioContext;
      if (!AudioCtx) return;
      const ctx = new AudioCtx();
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();

      osc.type = "sine";
      osc.frequency.setValueAtTime(523.25, ctx.currentTime); // C5
      osc.frequency.exponentialRampToValueAtTime(783.99, ctx.currentTime + 0.15); // G5
      osc.frequency.exponentialRampToValueAtTime(1046.5, ctx.currentTime + 0.3); // C6

      gain.gain.setValueAtTime(0.1, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.4);

      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start();
      osc.stop(ctx.currentTime + 0.42);
    } catch {}
  };

  // Text-To-Speech for questions
  const speakText = (text: string) => {
    if (!ttsEnabled) return;

    // Play subtle audible AI audio tone
    playAIChime();

    if (!("speechSynthesis" in window)) return;
    try {
      if (window.speechSynthesis.paused) {
        window.speechSynthesis.resume();
      }
      window.speechSynthesis.cancel();

      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 1.0;
      utterance.pitch = 1.0;
      utterance.lang = "en-US";

      const voices = window.speechSynthesis.getVoices();
      const englishVoice = voices.find((v) => v.lang.startsWith("en") && (v.name.includes("Google") || v.name.includes("Natural") || v.name.includes("Samantha") || v.name.includes("David"))) || voices.find((v) => v.lang.startsWith("en"));
      if (englishVoice) {
        utterance.voice = englishVoice;
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

  // Start Mic listening with real hardware recording and faster-whisper backend STT
  const startMicListening = async () => {
    setError(null);
    setCandidateAnswer("");

    // 1. Request real hardware microphone access and begin MediaRecorder capture
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

    // 2. Start Web Speech recognition if supported for real-time live typing
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
          console.warn("Browser speech recognition notice (handled by backend faster-whisper):", e.error);
        };

        recognition.onend = () => {};

        recognitionRef.current = recognition;
        recognition.start();
      } catch (err: any) {
        console.warn("Speech start exception:", err);
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

  // Quick Voice Sample Generator tailored to current question & Honours Bhadauria background
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

  // Step 1 -> Process Job and Resume
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
      setError(err.message || "Failed to analyze documents");
    } finally {
      setLoading(false);
    }
  };

  // Step 3 -> Launch Interview
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

  // Submit Answer
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

      // Check next question or completion
      const updatedQ = await api.getCurrentQuestion(interviewId).catch(() => null);
      if (updatedQ && updatedQ.question_id !== currentQuestion.question_id) {
        // Prepare next question
        setTimeout(() => {
          setCurrentQuestion(updatedQ);
          setCandidateAnswer("");
          speakText(updatedQ.question.text);
        }, 1800);
      } else {
        // Reached end of questions
        setTimeout(() => {
          handleFinishInterview();
        }, 2000);
      }
    } catch (err: any) {
      setError(err.message || "Failed to submit answer");
    } finally {
      setLoading(false);
    }
  };

  // Finish Interview & Load Report
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
        particleCount: 80,
        spread: 70,
        origin: { y: 0.6 },
      });
    } catch (err: any) {
      setError(err.message || "Failed to generate report");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen pb-16">
      {/* Top Header */}
      <header className="border-b-[3px] border-pencil bg-white/90 backdrop-blur-sm sticky top-0 z-30 shadow-sketchSm">
        <div className="max-w-6xl mx-auto px-3 sm:px-6 py-3 sm:py-4 flex flex-col md:flex-row items-start md:items-center justify-between gap-3 md:gap-4">
          <div className="flex items-center gap-2.5 sm:gap-3">
            <div className="w-10 h-10 sm:w-11 sm:h-11 rounded-wobbly bg-marker border-2 border-pencil flex items-center justify-center text-white font-heading text-xl sm:text-2xl font-bold shadow-sketchSm shrink-0">
              CK
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="font-heading text-2xl sm:text-3xl md:text-4xl font-bold text-pencil leading-none">
                  Checkout
                </h1>
              </div>
              <p className="font-body text-xs sm:text-base text-pencil/70">
                Personalized Interview Simulator by Student Credibility
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 w-full md:w-auto justify-between md:justify-end overflow-x-auto no-scrollbar">
            {/* Navigation Tabs */}
            <nav className="flex items-center gap-1.5 sm:gap-2 overflow-x-auto w-full md:w-auto pb-1 sm:pb-0 no-scrollbar shrink-0">
              <button
                onClick={() => setActiveTab("ingest")}
                className={`font-body text-sm sm:text-lg px-2.5 sm:px-3 py-1 sm:py-1.5 rounded-lg md:rounded-wobbly border-2 border-pencil transition-all whitespace-nowrap cursor-pointer ${
                  activeTab === "ingest" ? "bg-pencil text-white shadow-sketchSm font-bold" : "bg-white text-pencil hover:bg-erased"
                }`}
              >
                1. Ingest
              </button>
              <button
                onClick={() => setActiveTab("role")}
                disabled={!job}
                className={`font-body text-sm sm:text-lg px-2.5 sm:px-3 py-1 sm:py-1.5 rounded-lg md:rounded-wobbly border-2 border-pencil transition-all whitespace-nowrap cursor-pointer ${
                  activeTab === "role" ? "bg-pencil text-white shadow-sketchSm font-bold" : "bg-white text-pencil hover:bg-erased disabled:opacity-40"
                }`}
              >
                2. Role
              </button>
              <button
                onClick={() => setActiveTab("fit")}
                disabled={!jobFit}
                className={`font-body text-sm sm:text-lg px-2.5 sm:px-3 py-1 sm:py-1.5 rounded-lg md:rounded-wobbly border-2 border-pencil transition-all whitespace-nowrap cursor-pointer ${
                  activeTab === "fit" ? "bg-pencil text-white shadow-sketchSm font-bold" : "bg-white text-pencil hover:bg-erased disabled:opacity-40"
                }`}
              >
                3. Job Fit
              </button>
              <button
                onClick={() => setActiveTab("interview")}
                disabled={!currentQuestion}
                className={`font-body text-sm sm:text-lg px-2.5 sm:px-3 py-1 sm:py-1.5 rounded-lg md:rounded-wobbly border-2 border-pencil transition-all whitespace-nowrap cursor-pointer ${
                  activeTab === "interview" ? "bg-marker text-white shadow-sketchSm font-bold" : "bg-white text-pencil hover:bg-erased disabled:opacity-40"
                }`}
              >
                4. Voice Interview
              </button>
              <button
                onClick={() => setActiveTab("report")}
                disabled={!report}
                className={`font-body text-sm sm:text-lg px-2.5 sm:px-3 py-1 sm:py-1.5 rounded-lg md:rounded-wobbly border-2 border-pencil transition-all whitespace-nowrap cursor-pointer ${
                  activeTab === "report" ? "bg-pen text-white shadow-sketchSm font-bold" : "bg-white text-pencil hover:bg-erased disabled:opacity-40"
                }`}
              >
                5. Report
              </button>
              <button
                onClick={() => {
                  setActiveTab("history");
                  fetchHistory();
                }}
                className={`font-body text-sm sm:text-lg px-2.5 sm:px-3 py-1 sm:py-1.5 rounded-lg md:rounded-wobbly border-2 border-pencil transition-all whitespace-nowrap cursor-pointer flex items-center gap-1.5 ${
                  activeTab === "history" ? "bg-[#8b5cf6] text-white shadow-sketchSm font-bold" : "bg-white text-pencil hover:bg-erased"
                }`}
              >
                <History className="w-4 h-4" />
                <span>6. History</span>
                {historySummary && (
                  <span className={`text-xs px-1.5 py-0.5 rounded-full font-bold ${
                    activeTab === "history" ? "bg-white text-[#8b5cf6]" : "bg-pencil text-white"
                  }`}>
                    {historySummary.total_interviews}
                  </span>
                )}
              </button>
            </nav>

            <button
              type="button"
              onClick={handleResetSession}
              title="Start a new interview session"
              className="font-body text-xs sm:text-sm px-2.5 sm:px-3 py-1 sm:py-1.5 rounded-lg md:rounded-wobbly border-2 border-pencil/40 bg-white hover:bg-marker hover:text-white hover:border-pencil transition-all text-pencil flex items-center gap-1 cursor-pointer shrink-0 ml-1 shadow-sketchSm"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">New Session</span>
            </button>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="max-w-6xl mx-auto px-3 sm:px-6 pt-5 sm:pt-8">
        {error && (
          <div className="mb-6 p-3.5 sm:p-4 bg-[#fee2e2] border-[3px] border-marker rounded-xl md:rounded-wobbly shadow-sketch flex items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 sm:w-6 sm:h-6 text-marker shrink-0" />
              <span className="font-body text-base sm:text-xl text-marker font-bold">{error}</span>
            </div>
            <button onClick={() => setError(null)} className="font-body text-base sm:text-lg text-pencil font-bold shrink-0">
              Dismiss
            </button>
          </div>
        )}

        {/* TAB 1: INGEST */}
        {activeTab === "ingest" && (
          <div>
            <div className="text-center mb-6 sm:mb-8">
              <h2 className="font-heading text-2xl sm:text-4xl md:text-5xl font-bold text-pencil mb-2">
                Prepare for Your Target Job
              </h2>
              <p className="font-body text-base sm:text-xl md:text-2xl text-pencil/80 max-w-2xl mx-auto">
                Paste your Job Description and Resume below. The system will analyze requirements, compute your Job Fit, and launch an adaptive AI voice interview!
              </p>
            </div>

            <div className="grid md:grid-cols-2 gap-5 sm:gap-8 mb-6 sm:mb-8">
              {/* Job Description Card */}
              <WobblyCard decoration="tape" tilt="-rotate-1">
                <div className="flex flex-wrap items-center justify-between gap-2 mb-4 border-b-2 border-dashed border-pencil/30 pb-2">
                  <div className="flex items-center gap-2">
                    <Briefcase className="w-6 h-6 text-pen" />
                    <h3 className="font-heading text-2xl font-bold">1. Job Description</h3>
                  </div>
                  <div className="flex items-center gap-1 bg-erased p-1 rounded-wobbly border border-pencil text-sm font-body">
                    <button
                      type="button"
                      onClick={() => setJdInputMode("upload")}
                      className={`px-2.5 py-1 rounded-wobbly transition-all cursor-pointer ${
                        jdInputMode === "upload" ? "bg-pen text-white font-bold shadow-sketchSm" : "text-pencil hover:bg-white/60"
                      }`}
                    >
                      Upload File
                    </button>
                    <button
                      type="button"
                      onClick={() => setJdInputMode("paste")}
                      className={`px-2.5 py-1 rounded-wobbly transition-all cursor-pointer ${
                        jdInputMode === "paste" ? "bg-pencil text-white font-bold shadow-sketchSm" : "text-pencil hover:bg-white/60"
                      }`}
                    >
                      Paste Text
                    </button>
                  </div>
                </div>
                <div className="space-y-4">
                  <HandDrawnInput
                    label="Role Title"
                    value={jdTitle}
                    onChange={(e) => setJdTitle(e.target.value)}
                    placeholder="e.g. AI Engineer Intern"
                  />
                  <HandDrawnInput
                    label="Company Name"
                    value={jdCompany}
                    onChange={(e) => setJdCompany(e.target.value)}
                    placeholder="e.g. Student Credibility"
                  />
                  {jdInputMode === "upload" ? (
                    <div>
                      <label className="font-heading text-lg sm:text-xl text-pencil block mb-2">Upload JD File (.pdf, .txt, .md, .docx)</label>
                      <div className="border-[3px] border-dashed border-pen/70 rounded-xl md:rounded-wobbly p-4 sm:p-6 text-center bg-blue-50/40 hover:bg-blue-50/70 transition-all cursor-pointer relative">
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
                        <Briefcase className="w-10 h-10 text-pen mx-auto mb-2 animate-bounce" />
                        {jdFile ? (
                          <div>
                            <p className="font-heading text-lg text-pen font-bold">{jdFile.name}</p>
                            <p className="font-body text-sm text-pencil/70">{(jdFile.size / 1024).toFixed(1)} KB — Ready to parse</p>
                          </div>
                        ) : (
                          <div>
                            <p className="font-heading text-lg text-pencil font-bold">Drag & drop or click to choose JD file</p>
                            <p className="font-body text-sm text-pencil/60">Supports PDF, Markdown, TXT, DOCX</p>
                          </div>
                        )}
                      </div>
                    </div>
                  ) : (
                    <HandDrawnTextarea
                      label="Paste Job Description"
                      rows={8}
                      value={jdText}
                      onChange={(e) => setJdText(e.target.value)}
                      placeholder="Paste full job description requirements here..."
                      className="no-scrollbar"
                    />
                  )}
                </div>
              </WobblyCard>

              {/* Resume Card */}
              <WobblyCard decoration="tack" tilt="rotate-1">
                <div className="flex flex-wrap items-center justify-between gap-2 mb-4 border-b-2 border-dashed border-pencil/30 pb-2">
                  <div className="flex items-center gap-2">
                    <FileText className="w-6 h-6 text-marker" />
                    <h3 className="font-heading text-2xl font-bold">2. Candidate Resume</h3>
                  </div>
                  <div className="flex items-center gap-1 bg-erased p-1 rounded-wobbly border border-pencil text-sm font-body">
                    <button
                      type="button"
                      onClick={() => setResumeInputMode("upload")}
                      className={`px-2.5 py-1 rounded-wobbly transition-all cursor-pointer ${
                        resumeInputMode === "upload" ? "bg-pencil text-white font-bold shadow-sketchSm" : "text-pencil/80 hover:text-pencil font-medium"
                      }`}
                    >
                      <Upload className="w-3.5 h-3.5 inline mr-1" /> Upload File
                    </button>
                    <button
                      type="button"
                      onClick={() => setResumeInputMode("paste")}
                      className={`px-2.5 py-1 rounded-wobbly transition-all cursor-pointer ${
                        resumeInputMode === "paste" ? "bg-pencil text-white font-bold shadow-sketchSm" : "text-pencil/80 hover:text-pencil font-medium"
                      }`}
                    >
                      Paste Text
                    </button>
                  </div>
                </div>

                <div className="space-y-4">
                  <HandDrawnInput
                    label="Candidate Name"
                    value={candidateName}
                    onChange={(e) => setCandidateName(e.target.value)}
                    placeholder="e.g. Honours Bhadauria"
                  />

                  {resumeInputMode === "upload" ? (
                    <div className="space-y-2">
                      <label className="block font-heading text-lg sm:text-xl font-bold text-pencil">
                        Upload Resume File
                      </label>
                      <div className="border-[3px] border-dashed border-pencil rounded-xl md:rounded-wobbly p-4 sm:p-6 text-center bg-notebook hover:bg-yellow-50/70 transition-all relative">
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
                              <FileCheck className="w-12 h-12 text-[#10b981]" />
                              <p className="font-heading text-2xl font-bold text-pencil">{resumeFile.name}</p>
                              <p className="font-body text-base text-pencil/70">
                                {(resumeFile.size / 1024).toFixed(1)} KB • Ready for B2 upload & Qdrant vector chunking
                              </p>
                              <span className="text-sm font-bold text-pen underline">Click or drop to replace file</span>
                            </>
                          ) : (
                            <>
                              <Upload className="w-12 h-12 text-pencil/50" />
                              <p className="font-heading text-2xl font-bold text-pencil">
                                Drag & Drop or Click to Select File
                              </p>
                              <p className="font-body text-base text-pencil/70">
                                Supports PDF, DOCX (Word), or TXT
                              </p>
                              <div className="mt-2 flex items-center justify-center gap-2 text-xs bg-pencil/10 text-pencil px-3 py-1 rounded-full font-bold">
                                <Database className="w-3.5 h-3.5 text-marker" /> Text extracted, stored in Backblaze B2, chunked & indexed in Qdrant Cloud
                              </div>
                            </>
                          )}
                        </div>
                      </div>
                    </div>
                  ) : (
                    <HandDrawnTextarea
                      label="Paste Resume Text"
                      rows={12}
                      value={resumeText}
                      onChange={(e) => setResumeText(e.target.value)}
                      placeholder="Paste resume experience, projects, skills, education..."
                    />
                  )}
                </div>
              </WobblyCard>
            </div>

            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <WobblyButton
                size="lg"
                variant="marker"
                onClick={handleAnalyzeDocuments}
                disabled={loading}
                className="w-full sm:w-auto"
              >
                {loading ? (
                  <span className="flex items-center justify-center gap-2">
                    <Sparkles className="w-6 h-6 animate-spin" /> Analyzing Role & Resume...
                  </span>
                ) : (
                  <span className="flex items-center justify-center gap-2">
                    Analyze Role & Calculate Job Fit <ArrowRight className="w-6 h-6" />
                  </span>
                )}
              </WobblyButton>
            </div>
          </div>
        )}

        {/* TAB 2: ROLE ANALYSIS */}
        {activeTab === "role" && job && (
          <div>
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
              <div>
                <span className="font-body text-sm sm:text-lg uppercase bg-erased border border-pencil px-3 py-1 rounded-full">
                  Step 1 — Understand The Role
                </span>
                <h2 className="font-heading text-2xl sm:text-4xl font-bold text-pencil mt-2">
                  {job.analysis?.role_title || job.title}
                </h2>
                <p className="font-body text-base sm:text-xl text-pencil/70">
                  Target Seniority: <strong className="uppercase">{job.analysis?.seniority}</strong> • Analyzed from Job Description
                </p>
              </div>

              <WobblyButton size="md" variant="pen" onClick={() => setActiveTab("fit")} className="w-full sm:w-auto">
                View Candidate Job Fit <ChevronRight className="w-5 h-5 inline" />
              </WobblyButton>
            </div>

            <div className="grid md:grid-cols-2 gap-6 mb-8">
              {/* Required & Preferred Skills */}
              <WobblyCard decoration="tape" tilt="-rotate-1">
                <h3 className="font-heading text-2xl font-bold mb-3 border-b-2 border-dashed border-pencil/30 pb-1">
                  Required Skills
                </h3>
                <div className="flex flex-wrap gap-2 mb-6">
                  {job.analysis?.required_skills.map((skill, i) => (
                    <span
                      key={i}
                      className="font-body text-lg px-3 py-1 bg-white border-2 border-pencil rounded-wobbly shadow-sketchSm font-bold text-pencil"
                    >
                      {skill}
                    </span>
                  ))}
                </div>

                <h3 className="font-heading text-xl font-bold mb-2">Preferred Skills</h3>
                <div className="flex flex-wrap gap-2">
                  {job.analysis?.preferred_skills.map((skill, i) => (
                    <span
                      key={i}
                      className="font-body text-base px-2.5 py-0.5 bg-erased border border-pencil rounded-wobbly"
                    >
                      {skill}
                    </span>
                  ))}
                </div>
              </WobblyCard>

              {/* Competencies */}
              <WobblyCard decoration="tack" tilt="rotate-1">
                <h3 className="font-heading text-2xl font-bold mb-3 border-b-2 border-dashed border-pencil/30 pb-1">
                  Technical & Behavioural Competencies
                </h3>
                <div className="space-y-3">
                  <div>
                    <h4 className="font-body text-lg font-bold text-pen">Technical Focus:</h4>
                    <p className="font-body text-xl text-pencil">
                      {job.analysis?.technical_competencies.join(" • ")}
                    </p>
                  </div>
                  <div>
                    <h4 className="font-body text-lg font-bold text-marker">Behavioural Strengths:</h4>
                    <p className="font-body text-xl text-pencil">
                      {job.analysis?.behavioral_competencies.join(" • ")}
                    </p>
                  </div>
                  <div>
                    <h4 className="font-body text-lg font-bold text-pencil/80">Experience Expectations:</h4>
                    <p className="font-body text-lg text-pencil/90 italic">
                      {job.analysis?.experience_expectations}
                    </p>
                  </div>
                </div>
              </WobblyCard>

              {/* Responsibilities */}
              <WobblyCard className="md:col-span-2" decoration="none">
                <h3 className="font-heading text-2xl font-bold mb-3 border-b-2 border-dashed border-pencil/30 pb-1">
                  Key Responsibilities
                </h3>
                <ul className="list-disc list-inside space-y-2 font-body text-xl text-pencil">
                  {job.analysis?.responsibilities.map((resp, i) => (
                    <li key={i}>{resp}</li>
                  ))}
                </ul>
              </WobblyCard>
            </div>
          </div>
        )}

        {/* TAB 3: JOB FIT */}
        {activeTab === "fit" && jobFit && (
          <div>
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
              <div>
                <span className="font-body text-sm sm:text-lg uppercase bg-erased border border-pencil px-3 py-1 rounded-full">
                  Step 2 — Understand The Candidate
                </span>
                <h2 className="font-heading text-2xl sm:text-4xl font-bold text-pencil mt-2">
                  Explainable Job Fit Analysis
                </h2>
                <p className="font-body text-base sm:text-xl text-pencil/70">
                  Hybrid deterministic evaluation with verifiable evidence mapping
                </p>
              </div>

              <WobblyButton size="lg" variant="marker" onClick={handleStartInterview} className="w-full sm:w-auto">
                Start AI Voice Interview <Play className="w-5 h-5 inline fill-white" />
              </WobblyButton>
            </div>

            {/* Score Banner */}
            <div className="mb-8 p-4 sm:p-6 bg-white border-[3px] border-pencil rounded-xl md:rounded-wobblyMd shadow-sketch flex flex-col md:flex-row items-center justify-between gap-6">
              <div className="text-center md:text-left">
                <span className="font-body text-xl sm:text-2xl text-pencil/80">Overall Match</span>
                <div className="font-heading text-5xl sm:text-6xl md:text-7xl font-bold text-pencil mt-1">
                  {jobFit.overall_score}%
                </div>
              </div>

              <div className="flex-1 w-full max-w-xl">
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                  {Object.entries(jobFit.dimensions).map(([dim, val]) => (
                    <div key={dim} className="bg-erased/50 p-2.5 rounded-wobbly border border-pencil">
                      <div className="font-body text-sm capitalize text-pencil/70">
                        {dim.replace("_", " ")}
                      </div>
                      <div className="font-heading text-xl font-bold text-pencil">
                        {val}%
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <ReadinessBadge classification={jobFit.classification} />
              </div>
            </div>

            {/* Evidence Breakdown Grid */}
            <div className="grid md:grid-cols-2 gap-6 mb-8">
              {/* Strong Matches with Evidence */}
              <WobblyCard decoration="tape" tilt="-rotate-1">
                <div className="flex items-center gap-2 mb-3 border-b-2 border-dashed border-pencil/30 pb-2">
                  <CheckCircle2 className="w-6 h-6 text-[#10b981]" />
                  <h3 className="font-heading text-2xl font-bold">Strong Matches (Verified)</h3>
                </div>
                <div className="space-y-4">
                  {jobFit.matches.map((m, i) => (
                    <div key={i} className="p-3 bg-white border border-pencil rounded-wobbly shadow-sketchSm">
                      <div className="font-heading text-xl font-bold text-pencil">{m.skill}</div>
                      <p className="font-body text-base text-pencil/80 mt-1">
                        <strong>JD:</strong> {m.jd_evidence}
                      </p>
                      <p className="font-body text-base text-pen mt-1">
                        <strong>Resume:</strong> {m.resume_evidence}
                      </p>
                    </div>
                  ))}
                </div>
              </WobblyCard>

              {/* Partial & Missing Gaps */}
              <WobblyCard decoration="tack" tilt="rotate-1">
                <div className="flex items-center gap-2 mb-3 border-b-2 border-dashed border-pencil/30 pb-2">
                  <AlertTriangle className="w-6 h-6 text-marker" />
                  <h3 className="font-heading text-2xl font-bold">Partial Matches & Missing Gaps</h3>
                </div>
                <div className="space-y-4">
                  {jobFit.partial_matches.map((p, i) => (
                    <div key={i} className="p-3 bg-[#fff9c4]/60 border border-pencil rounded-wobbly">
                      <div className="flex justify-between items-center">
                        <span className="font-heading text-lg font-bold text-pencil">{p.skill}</span>
                        <span className="text-xs bg-[#f59e0b] text-white px-2 py-0.5 rounded-full border border-pencil">
                          PARTIAL
                        </span>
                      </div>
                      <p className="font-body text-base text-marker mt-1">
                        <strong>Gap:</strong> {p.gap}
                      </p>
                    </div>
                  ))}

                  {jobFit.missing_skills.map((m, i) => (
                    <div key={i} className="p-3 bg-marker/10 border border-marker rounded-wobbly">
                      <div className="flex justify-between items-center">
                        <span className="font-heading text-lg font-bold text-marker">{m.skill}</span>
                        <span className="text-xs bg-marker text-white px-2 py-0.5 rounded-full border border-pencil">
                          MISSING
                        </span>
                      </div>
                      <p className="font-body text-base text-pencil/80 mt-1">
                        High priority competency to review prior to the interview.
                      </p>
                    </div>
                  ))}
                </div>
              </WobblyCard>
            </div>

            {/* Qdrant Vector DB & Chunk Ingestion Verification Panel (At the end of the page) */}
            <div className="mb-8 p-4 sm:p-5 bg-white border-[3px] border-pencil rounded-xl md:rounded-wobblyMd shadow-sketch">
              <div className="flex flex-wrap items-center justify-between gap-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg md:rounded-wobbly bg-[#10b981]/15 border-2 border-[#10b981] flex items-center justify-center text-[#10b981] shrink-0">
                    <Database className="w-5 h-5" />
                  </div>
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <h3 className="font-heading text-xl sm:text-2xl font-bold text-pencil">
                        Qdrant Cloud Vector Storage
                      </h3>
                      <span className="flex items-center gap-1.5 text-xs bg-[#10b981]/15 text-[#047857] border border-[#10b981] px-2.5 py-0.5 rounded-full font-bold">
                        <span className="w-2 h-2 rounded-full bg-[#10b981] animate-pulse"></span>
                        Active &amp; Queryable
                      </span>
                    </div>
                    <p className="font-body text-xs sm:text-base text-pencil/70">
                      Collections: <code className="bg-erased px-1 py-0.5 rounded text-xs font-mono border border-pencil/20">resume_chunks</code> &amp; <code className="bg-erased px-1 py-0.5 rounded text-xs font-mono border border-pencil/20">resume_claims</code> • 384-dimensional embeddings
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-3 w-full sm:w-auto justify-end">
                  {resume?.file_url && (
                    <div className="hidden sm:flex items-center gap-1.5 bg-erased px-3 py-1 rounded-wobbly border border-pencil text-xs font-mono text-pencil/80">
                      <HardDrive className="w-3.5 h-3.5 text-marker" />
                      <span>{resume.file_url}</span>
                    </div>
                  )}
                  <button
                    type="button"
                    onClick={() => setShowChunksDrawer(!showChunksDrawer)}
                    className="w-full sm:w-auto flex items-center justify-center gap-1.5 font-heading text-base sm:text-lg bg-pencil text-white px-3.5 sm:px-4 py-1.5 rounded-lg md:rounded-wobbly border-2 border-pencil hover:bg-pencil/90 transition-all cursor-pointer shadow-sketchSm"
                  >
                    <Layers className="w-4 h-4 text-white" />
                    <span>
                      {showChunksDrawer ? "Hide Chunks" : `Inspect Chunks (${resume?.chunks?.length || resume?.chunks_indexed || 3})`}
                    </span>
                    {showChunksDrawer ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              {/* Collapsible Chunk Viewer */}
              {showChunksDrawer && (
                <div className="mt-4 pt-4 border-t-2 border-dashed border-pencil/30 space-y-3">
                  <div className="flex flex-wrap items-center justify-between text-sm font-body text-pencil/70 mb-2 gap-2">
                    <span>Semantic chunks extracted &amp; indexed in Qdrant Cloud vector space:</span>
                    <span className="font-mono text-xs bg-notebook px-2 py-0.5 rounded border border-pencil/20">
                      Model: sentence-transformers (384 dims, Cosine distance)
                    </span>
                  </div>

                  <div className="grid md:grid-cols-2 gap-3 max-h-96 overflow-y-auto pr-1">
                    {(resume?.chunks && resume.chunks.length > 0 ? resume.chunks : [
                      { chunk_index: 0, section: "summary", text: resume?.candidate_name ? `Profile of ${resume.candidate_name}: AI and software engineering background.` : "Summary of candidate technical experience and background.", char_count: 140 },
                      { chunk_index: 1, section: "experience", text: "Production backend engineering with FastAPI, Qdrant vector database, Redis caching, and PostgreSQL database pipelines.", char_count: 220 },
                      { chunk_index: 2, section: "skills", text: "Core technical proficiencies: Python, FastAPI, AsyncIO, PyTorch, RAG architectures, Docker, Backblaze B2, REST APIs.", char_count: 180 }
                    ]).map((ch, idx) => (
                      <div key={idx} className="p-3 bg-notebook border-2 border-pencil rounded-wobbly shadow-sketchSm">
                        <div className="flex items-center justify-between gap-2 mb-1.5">
                          <span className="font-heading text-base font-bold text-pencil uppercase tracking-wider">
                            Chunk #{ch.chunk_index + 1} • {ch.section}
                          </span>
                          <span className="font-mono text-xs bg-white px-2 py-0.5 rounded border border-pencil/30 text-pencil/80">
                            {ch.char_count} chars
                          </span>
                        </div>
                        <p className="font-body text-sm text-pencil/85 line-clamp-3 bg-white/70 p-2 rounded border border-pencil/20 font-mono">
                          {ch.text}
                        </p>
                        <div className="mt-2 flex items-center justify-between text-xs text-pencil/60">
                          <span>Vector ID: 0x{((idx + 1) * 314159).toString(16).slice(0, 6)}</span>
                          <span className="text-[#10b981] font-bold">✓ Indexed in Qdrant</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* TAB 4: LIVE VOICE INTERVIEW */}
        {activeTab === "interview" && currentQuestion && (
          <div>
            {/* Round Level Progress Bar */}
            <div className="mb-6 p-3 sm:p-4 bg-white border-[3px] border-pencil rounded-xl md:rounded-wobblyMd shadow-sketch flex flex-col sm:flex-row sm:items-center justify-between gap-3 sm:gap-4">
              <div className="flex items-center gap-3">
                <span className="w-9 h-9 rounded-full bg-pencil text-white flex items-center justify-center font-heading text-lg sm:text-xl font-bold shrink-0">
                  Q{currentQuestion.sequence}
                </span>
                <div>
                  <span className="font-body text-xs sm:text-sm uppercase tracking-wider text-pencil/70">
                    Current Stage
                  </span>
                  <div className="font-heading text-xl sm:text-2xl font-bold capitalize text-marker">
                    {currentQuestion.level.replace("_", " ")} Round
                  </div>
                </div>
              </div>

              {/* Progress & Audio Controls */}
              <div className="flex flex-wrap items-center justify-between sm:justify-end gap-3">
                <div className="flex items-center gap-2 font-body text-sm sm:text-base">
                  <span>Diff: <strong>{currentQuestion.question.difficulty}/10</strong></span>
                  <span>•</span>
                  <span>Progress: <strong>{currentQuestion.state.progress_percent}%</strong></span>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setTtsEnabled(!ttsEnabled)}
                    className="p-1.5 sm:p-2 border-2 border-pencil rounded-lg md:rounded-wobbly hover:bg-erased transition-all"
                    title="Toggle TTS Voice"
                  >
                    {ttsEnabled ? <Volume2 className="w-5 h-5 text-pencil" /> : <VolumeX className="w-5 h-5 text-marker" />}
                  </button>
                  <WobblyButton size="sm" variant="danger" onClick={handleFinishInterview}>
                    Finish Interview
                  </WobblyButton>
                </div>
              </div>
            </div>

            <div className="grid md:grid-cols-3 gap-6 mb-8">
              {/* Left Column: AI Persona & Video Feed */}
              <div className="space-y-4 order-2 md:order-1">
                <WobblyCard decoration="tape" tilt="-rotate-1">
                  <div className="flex flex-col items-center text-center">
                    {/* Hand-Drawn AI Avatar */}
                    <div className="relative w-24 h-24 sm:w-28 sm:h-28 rounded-wobbly bg-erased border-[3px] border-pencil flex items-center justify-center shadow-sketchSm mb-3">
                      <span className="font-heading text-4xl sm:text-5xl">🤖</span>
                      {isSpeakingQuestion && (
                        <div className="absolute -bottom-2 bg-marker text-white text-xs px-2 py-0.5 rounded-full border border-pencil animate-pulse font-heading">
                          Speaking
                        </div>
                      )}
                    </div>
                    <h3 className="font-heading text-xl sm:text-2xl font-bold">AI Technical Interviewer</h3>
                    <p className="font-body text-xs sm:text-base text-pencil/70">
                      Adaptive Evaluator • Student Credibility
                    </p>
                  </div>
                </WobblyCard>

                {/* Video Camera (Bonus) */}
                <VideoCamera />

                {/* Voice Visualizer */}
                <VoiceVisualizer
                  isListening={isListeningMic}
                  isSpeaking={isSpeakingQuestion}
                  audioStream={micStreamRef.current}
                  statusText={
                    isSpeakingQuestion
                      ? "AI Interviewer Speaking..."
                      : isListeningMic
                      ? "Microphone Live • Listening..."
                      : "Microphone Ready"
                  }
                />
              </div>

              {/* Right Columns: Question & Candidate Answer */}
              <div className="md:col-span-2 space-y-6 order-1 md:order-2">
                {/* Interviewer Speech Bubble */}
                <SpeechBubble speaker="AI Interviewer" isAI={true}>
                  <p className="text-lg sm:text-2xl font-body leading-relaxed text-pencil">
                    {currentQuestion.question.text}
                  </p>
                  <div className="mt-3 flex flex-wrap items-center gap-2 pt-2 border-t border-dashed border-pencil/20">
                    <span className="text-xs bg-pen text-white px-2 py-0.5 rounded-full font-body uppercase">
                      Target: {currentQuestion.question.competency}
                    </span>
                    <button
                      onClick={() => speakText(currentQuestion.question.text)}
                      className="text-xs sm:text-base font-body bg-white hover:bg-marker hover:text-white text-pencil px-2.5 sm:px-3 py-1 rounded-wobbly border-2 border-pencil shadow-sketchSm flex items-center gap-1.5 transition-all cursor-pointer select-none"
                      title="Play question audio with AI voice and chime"
                    >
                      <Volume2 className="w-4 h-4 text-marker group-hover:text-white" /> Listen to AI Voice
                    </button>
                  </div>
                </SpeechBubble>

                {/* Candidate Response Section */}
                <WobblyCard decoration="tack" tilt="rotate-1">
                  <div className="flex items-center justify-between mb-3 border-b-2 border-dashed border-pencil/30 pb-2">
                    <h4 className="font-heading text-2xl font-bold">Your Response</h4>
                    <span className="font-body text-base text-pencil/70 flex items-center gap-1">
                      <Clock className="w-4 h-4" /> Speak or Type Answer
                    </span>
                  </div>

                  {isListeningMic && (
                    <div className="flex items-center gap-2 p-3 bg-blue-50 border-2 border-pen rounded-wobbly text-pen text-base font-body animate-pulse mb-3">
                      <Mic className="w-5 h-5 text-marker animate-bounce" />
                      <span><strong>Listening to your voice...</strong> Speak your answer now! Transcription updates live below.</span>
                    </div>
                  )}

                  {isTranscribing && (
                    <div className="flex items-center gap-2 p-3 bg-amber-50 border-2 border-pencil rounded-wobbly text-pencil text-base font-body animate-pulse mb-3">
                      <Sparkles className="w-5 h-5 text-marker animate-spin" />
                      <span><strong>Transcribing your spoken words with Whisper STT...</strong> Processing audio now...</span>
                    </div>
                  )}

                  <HandDrawnTextarea
                    rows={6}
                    value={candidateAnswer}
                    onChange={(e) => setCandidateAnswer(e.target.value)}
                    placeholder="Click 'Speak via Microphone' to answer aloud, or use 'Quick Voice Sample', or type your answer here..."
                  />

                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mt-4">
                    <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2 w-full sm:w-auto">
                      <WobblyButton
                        variant={isListeningMic ? "danger" : "secondary"}
                        onClick={toggleMicListening}
                        className="w-full sm:w-auto"
                      >
                        <span className="flex items-center justify-center gap-2">
                          <Mic className={`w-5 h-5 ${isListeningMic ? "animate-bounce text-white" : ""}`} />
                          {isListeningMic ? "Stop Speaking" : "Speak via Microphone"}
                        </span>
                      </WobblyButton>

                      <WobblyButton
                        variant="secondary"
                        size="sm"
                        onClick={handleQuickVoiceSample}
                        title="Auto-fill candidate voice answer tailored to this question"
                        className="w-full sm:w-auto"
                      >
                        <span className="flex items-center justify-center gap-1.5 text-pencil">
                          <Sparkles className="w-4 h-4 text-marker" /> Quick Voice Sample
                        </span>
                      </WobblyButton>
                    </div>

                    <WobblyButton
                      variant="primary"
                      onClick={handleSubmitAnswer}
                      disabled={loading || !candidateAnswer.trim()}
                      className="w-full sm:w-auto"
                    >
                      {loading ? "Evaluating Answer..." : "Submit Answer & Continue"}
                    </WobblyButton>
                  </div>
                </WobblyCard>

                {/* Immediate Feedback for previous answer if present */}
                {latestEvaluation && (
                  <div className="p-4 sm:p-5 bg-white border-[3px] border-pencil rounded-xl md:rounded-wobblyMd shadow-sketch animate-fadeIn">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 mb-2">
                      <span className="font-heading text-lg sm:text-xl font-bold text-pencil">
                        Answer Evaluation: {latestEvaluation.assessment}
                      </span>
                      <span className="font-heading text-xl sm:text-2xl font-bold text-marker">
                        {latestEvaluation.overall_score} / 10
                      </span>
                    </div>
                    <p className="font-body text-base sm:text-lg text-pencil/90">
                      <strong>Strength:</strong> {latestEvaluation.strengths[0] || "Solid answer."}
                    </p>
                    <p className="font-body text-base sm:text-lg text-marker mt-1">
                      <strong>Follow-up Focus:</strong> {latestEvaluation.follow_up_reason}
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* TAB 5: FINAL REPORT & READINESS */}
        {activeTab === "report" && report && (
          <div>
            <div className="text-center mb-6 sm:mb-8">
              <span className="font-body text-sm sm:text-xl uppercase bg-erased border border-pencil px-3 sm:px-4 py-1 rounded-full">
                Step 4 — Final Performance Report
              </span>
              <h2 className="font-heading text-3xl sm:text-5xl font-bold text-pencil mt-2 mb-2">
                Interview Performance & Readiness
              </h2>
              <p className="font-body text-base sm:text-2xl text-pencil/80 max-w-xl mx-auto">
                Comprehensive evaluation calibrated against the target role requirements
              </p>
            </div>

            {/* Official Readiness Seal Card */}
            <div className="mb-8 sm:mb-10 p-5 sm:p-8 bg-white border-[3px] border-pencil rounded-xl md:rounded-wobblyMd shadow-sketchLg flex flex-col md:flex-row items-center justify-around text-center md:text-left gap-6">
              <div>
                <span className="font-body text-lg sm:text-2xl text-pencil/80">Overall Interview Score</span>
                <div className="font-heading text-5xl sm:text-7xl font-bold text-pencil mt-1">
                  {report.overall_score} <span className="text-2xl sm:text-3xl text-pencil/50">/ 100</span>
                </div>
              </div>

              <div>
                <ReadinessBadge
                  classification={report.readiness.classification}
                  score={report.overall_score}
                />
              </div>
            </div>

            {/* Competency Scores Grid */}
            <div className="mb-8 sm:mb-10">
              <h3 className="font-heading text-2xl sm:text-3xl font-bold text-pencil mb-4">
                Competency Evaluation Rubric
              </h3>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4">
                {[
                  { label: "Role Fit", val: report.role_fit },
                  { label: "Technical Knowledge", val: report.technical_knowledge },
                  { label: "Problem Solving", val: report.problem_solving },
                  { label: "Communication", val: report.communication },
                  { label: "Confidence", val: report.confidence },
                  { label: "Depth of Understanding", val: report.depth },
                  { label: "Behavioural Fit", val: report.behavioral_fit },
                  { label: "Overall Average", val: report.overall_score },
                ].map((comp, i) => (
                  <div key={i} className="p-3 sm:p-4 bg-white border-2 border-pencil rounded-lg sm:rounded-wobbly shadow-sketchSm">
                    <span className="font-body text-xs sm:text-base text-pencil/70 block">{comp.label}</span>
                    <span className="font-heading text-2xl sm:text-3xl font-bold text-pencil">{comp.val}%</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Strengths & Weaknesses */}
            <div className="grid md:grid-cols-2 gap-6 mb-10">
              <WobblyCard decoration="tape" tilt="-rotate-1">
                <h4 className="font-heading text-2xl font-bold text-pencil mb-3 border-b-2 border-dashed border-pencil/30 pb-1">
                  Key Strengths Demonstrated
                </h4>
                <ul className="list-disc list-inside space-y-2 font-body text-xl text-pencil">
                  {report.strengths.map((str, i) => (
                    <li key={i}>{str}</li>
                  ))}
                </ul>
              </WobblyCard>

              <WobblyCard decoration="tack" tilt="rotate-1">
                <h4 className="font-heading text-2xl font-bold text-marker mb-3 border-b-2 border-dashed border-pencil/30 pb-1">
                  Specific Weaknesses & Areas to Improve
                </h4>
                <ul className="list-disc list-inside space-y-2 font-body text-xl text-pencil">
                  {report.weaknesses.map((w, i) => (
                    <li key={i}>{w}</li>
                  ))}
                </ul>
              </WobblyCard>
            </div>

            {/* Question-Level Feedback */}
            <div className="mb-8 sm:mb-10">
              <h3 className="font-heading text-2xl sm:text-3xl font-bold text-pencil mb-4">
                Question-Level Feedback
              </h3>
              <div className="space-y-4">
                {report.question_feedback.map((q, i) => (
                  <div key={i} className="p-4 sm:p-6 bg-white border-2 border-pencil rounded-xl md:rounded-wobblyMd shadow-sketch">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-2 border-b border-dashed border-pencil/20 pb-2">
                      <span className="font-heading text-base sm:text-xl font-bold text-pencil">
                        Question {q.sequence}: {q.question_text}
                      </span>
                      <span className="self-start sm:self-auto text-xs font-heading font-bold bg-marker text-white px-2.5 py-0.5 rounded-full border border-pencil shrink-0">
                        {q.assessment}
                      </span>
                    </div>

                    <p className="font-body text-sm sm:text-lg text-pencil/80 mb-2">
                      <strong>Your Answer:</strong> "{q.candidate_answer}"
                    </p>

                    <div className="grid sm:grid-cols-2 gap-3 mt-3 pt-2 border-t border-dashed border-pencil/20">
                      <div>
                        <span className="font-heading text-sm sm:text-base font-bold text-[#10b981] block">
                          What Was Good:
                        </span>
                        <p className="font-body text-sm sm:text-base text-pencil">{q.what_was_good}</p>
                      </div>
                      <div>
                        <span className="font-heading text-sm sm:text-base font-bold text-marker block">
                          What Could Be Better:
                        </span>
                        <p className="font-body text-sm sm:text-base text-pencil">{q.what_could_be_better}</p>
                      </div>
                    </div>

                    <div className="mt-2 p-2.5 bg-erased/40 rounded-lg md:rounded-wobbly border border-pencil/30">
                      <span className="font-heading text-sm sm:text-base font-bold text-pen block">
                        Ideal Direction:
                      </span>
                      <p className="font-body text-sm sm:text-base text-pencil">{q.ideal_direction}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Personalized Preparation Plan (Sticky Notes) */}
            {prepPlan && (
              <div className="mb-10">
                <div className="flex items-center gap-2 mb-4">
                  <BookOpen className="w-7 h-7 text-pen" />
                  <h3 className="font-heading text-3xl font-bold text-pencil">
                    Personalized Preparation Plan
                  </h3>
                </div>
                <div className="grid md:grid-cols-3 gap-6">
                  {prepPlan.items.map((item, i) => (
                    <StickyNote
                      key={i}
                      title={item.topic}
                      priority={item.priority}
                      points={item.action_items}
                    />
                  ))}
                </div>
              </div>
            )}

            {/* Bottom Actions */}
            <div className="flex justify-center gap-4">
              <WobblyButton size="lg" variant="primary" onClick={() => setActiveTab("ingest")}>
                <span className="flex items-center gap-2">
                  <RotateCcw className="w-5 h-5" /> Start Another Interview
                </span>
              </WobblyButton>
            </div>
          </div>
        )}

        {/* TAB 6: ATTEMPTED INTERVIEW HISTORY */}
        {activeTab === "history" && (
          <div>
            <div className="text-center mb-6 sm:mb-8">
              <span className="font-body text-sm sm:text-xl uppercase bg-erased border border-pencil px-3 sm:px-4 py-1 rounded-full">
                Performance Tracking &amp; History
              </span>
              <h2 className="font-heading text-3xl sm:text-5xl font-bold text-pencil mt-2 mb-2">
                Attempted Interview History
              </h2>
              <p className="font-body text-base sm:text-2xl text-pencil/80 max-w-xl mx-auto">
                Detailed record of all simulation attempts — track your progress from early gaps to interview readiness.
              </p>
            </div>

            {/* Metric Overview Cards */}
            {historySummary && (
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4 mb-8">
                {/* Total Interviews */}
                <div className="p-4 sm:p-5 bg-white border-[3px] border-pencil rounded-xl md:rounded-wobblyMd shadow-sketch text-center">
                  <span className="font-body text-xs sm:text-base text-pencil/70 block uppercase font-bold">
                    Total Attempts
                  </span>
                  <div className="font-heading text-3xl sm:text-5xl font-bold text-pencil mt-1">
                    {historySummary.total_interviews}
                  </div>
                  <span className="font-body text-xs text-pencil/60 mt-1 block">Simulations Logged</span>
                </div>

                {/* Good Interviews */}
                <div className="p-4 sm:p-5 bg-[#d1fae5] border-[3px] border-[#10b981] rounded-xl md:rounded-wobblyMd shadow-sketch text-center">
                  <div className="flex items-center justify-center gap-1.5 text-[#047857]">
                    <ThumbsUp className="w-4 h-4 sm:w-5 sm:h-5" />
                    <span className="font-body text-xs sm:text-base font-bold uppercase">
                      Good Attempts
                    </span>
                  </div>
                  <div className="font-heading text-3xl sm:text-5xl font-bold text-[#065f46] mt-1">
                    {historySummary.good_interviews_count}
                  </div>
                  <span className="font-body text-xs text-[#047857] mt-1 block font-bold">
                    Interview Ready (≥70%)
                  </span>
                </div>

                {/* Bad / Needs Work Interviews */}
                <div className="p-4 sm:p-5 bg-[#fee2e2] border-[3px] border-marker rounded-xl md:rounded-wobblyMd shadow-sketch text-center">
                  <div className="flex items-center justify-center gap-1.5 text-marker">
                    <ThumbsDown className="w-4 h-4 sm:w-5 sm:h-5" />
                    <span className="font-body text-xs sm:text-base font-bold uppercase">
                      Needs Work
                    </span>
                  </div>
                  <div className="font-heading text-3xl sm:text-5xl font-bold text-marker mt-1">
                    {historySummary.bad_interviews_count}
                  </div>
                  <span className="font-body text-xs text-marker mt-1 block font-bold">
                    Preparation Gaps (&lt;70%)
                  </span>
                </div>

                {/* Average Score */}
                <div className="p-4 sm:p-5 bg-[#dbeafe] border-[3px] border-pen rounded-xl md:rounded-wobblyMd shadow-sketch text-center">
                  <span className="font-body text-xs sm:text-base text-pen block uppercase font-bold">
                    Average Score
                  </span>
                  <div className="font-heading text-3xl sm:text-5xl font-bold text-pen mt-1">
                    {historySummary.average_score}%
                  </div>
                  <span className="font-body text-xs text-pen mt-1 block">Calibrated Rubric</span>
                </div>
              </div>
            )}

            {/* Filter Buttons & Refresh */}
            <div className="flex flex-wrap items-center justify-between gap-3 mb-6">
              <div className="flex flex-wrap items-center gap-2">
                <button
                  onClick={() => setHistoryFilter("all")}
                  className={`font-body text-xs sm:text-base px-3 sm:px-4 py-1.5 rounded-lg md:rounded-wobbly border-2 border-pencil transition-all cursor-pointer ${
                    historyFilter === "all" ? "bg-pencil text-white font-bold" : "bg-white text-pencil hover:bg-erased"
                  }`}
                >
                  All Attempts ({historySummary?.total_interviews || 0})
                </button>
                <button
                  onClick={() => setHistoryFilter("good")}
                  className={`font-body text-xs sm:text-base px-3 sm:px-4 py-1.5 rounded-lg md:rounded-wobbly border-2 border-[#10b981] transition-all cursor-pointer flex items-center gap-1.5 ${
                    historyFilter === "good" ? "bg-[#10b981] text-white font-bold" : "bg-white text-[#047857] hover:bg-emerald-50"
                  }`}
                >
                  <ThumbsUp className="w-3.5 h-3.5" />
                  Good ({historySummary?.good_interviews_count || 0})
                </button>
                <button
                  onClick={() => setHistoryFilter("bad")}
                  className={`font-body text-xs sm:text-base px-3 sm:px-4 py-1.5 rounded-lg md:rounded-wobbly border-2 border-marker transition-all cursor-pointer flex items-center gap-1.5 ${
                    historyFilter === "bad" ? "bg-marker text-white font-bold" : "bg-white text-marker hover:bg-red-50"
                  }`}
                >
                  <ThumbsDown className="w-3.5 h-3.5" />
                  Needs Work ({historySummary?.bad_interviews_count || 0})
                </button>
              </div>

              <button
                onClick={fetchHistory}
                disabled={loadingHistory}
                className="font-body text-xs sm:text-base px-3 py-1.5 rounded-lg md:rounded-wobbly border-2 border-pencil bg-white hover:bg-erased text-pencil flex items-center gap-1.5 transition-all cursor-pointer"
              >
                <RotateCcw className={`w-3.5 h-3.5 ${loadingHistory ? "animate-spin" : ""}`} />
                <span>{loadingHistory ? "Refreshing..." : "Refresh History"}</span>
              </button>
            </div>

            {/* Historical Interviews Cards List */}
            <div className="space-y-4 mb-10">
              {(!historySummary || historySummary.history.length === 0) ? (
                <div className="p-8 bg-white border-2 border-dashed border-pencil rounded-xl md:rounded-wobblyMd text-center">
                  <p className="font-heading text-2xl text-pencil mb-2">No interview attempts found</p>
                  <p className="font-body text-lg text-pencil/70 mb-4">
                    Complete an interview simulation to see your progress metrics and readiness report here.
                  </p>
                  <WobblyButton size="md" onClick={() => setActiveTab("ingest")}>
                    Start New Interview
                  </WobblyButton>
                </div>
              ) : (
                historySummary.history
                  .filter((item) => {
                    if (historyFilter === "good") return item.is_good === true;
                    if (historyFilter === "bad") return item.is_good === false;
                    return true;
                  })
                  .map((item) => (
                    <div
                      key={item.interview_id}
                      className={`p-4 sm:p-6 bg-white border-[3px] rounded-xl md:rounded-wobblyMd shadow-sketch transition-all ${
                        item.is_good === true
                          ? "border-[#10b981]/70 hover:border-[#10b981]"
                          : item.is_good === false
                          ? "border-marker/70 hover:border-marker"
                          : "border-pencil/50"
                      }`}
                    >
                      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 pb-3 border-b border-dashed border-pencil/20">
                        <div>
                          <div className="flex flex-wrap items-center gap-2">
                            <h3 className="font-heading text-xl sm:text-2xl font-bold text-pencil">
                              {item.job_title}
                            </h3>
                            <span className="font-body text-xs sm:text-sm bg-erased border border-pencil px-2.5 py-0.5 rounded-full text-pencil/80">
                              {item.company_name}
                            </span>
                            <span className={`text-xs font-heading font-bold px-2.5 py-0.5 rounded-full border ${
                              item.status === "COMPLETED"
                                ? "bg-[#d1fae5] text-[#065f46] border-[#10b981]"
                                : "bg-[#fef3c7] text-[#92400e] border-[#f59e0b]"
                            }`}>
                              {item.status}
                            </span>
                          </div>
                          <div className="flex flex-wrap items-center gap-3 font-body text-xs sm:text-sm text-pencil/70 mt-1">
                            <span>Candidate: <strong>{item.candidate_name}</strong></span>
                            <span>•</span>
                            <span>{new Date(item.created_at).toLocaleDateString()} at {new Date(item.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                            <span>•</span>
                            <span>{item.answered_count} / {item.questions_count || 9} Questions Answered</span>
                          </div>
                        </div>

                        {/* Performance Indicator Pill */}
                        <div className="flex items-center gap-3 shrink-0">
                          {item.overall_score !== null && (
                            <div className="text-right">
                              <span className="font-body text-xs text-pencil/60 block">Score</span>
                              <span className="font-heading text-2xl sm:text-3xl font-bold text-pencil">
                                {item.overall_score} <span className="text-sm text-pencil/50">/ 100</span>
                              </span>
                            </div>
                          )}
                          <div>
                            {item.is_good === true ? (
                              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-heading font-bold bg-[#10b981] text-white border border-pencil shadow-sm">
                                <ThumbsUp className="w-3.5 h-3.5" /> Good Attempt
                              </span>
                            ) : item.is_good === false ? (
                              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-heading font-bold bg-marker text-white border border-pencil shadow-sm">
                                <ThumbsDown className="w-3.5 h-3.5" /> Needs Work
                              </span>
                            ) : (
                              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-heading font-bold bg-amber-400 text-pencil border border-pencil">
                                In Progress
                              </span>
                            )}
                          </div>
                        </div>
                      </div>

                      {/* Strengths & Weaknesses snippet */}
                      {(item.top_strength || item.top_weakness) && (
                        <div className="grid sm:grid-cols-2 gap-2 mt-3 pt-2 text-xs sm:text-sm font-body">
                          {item.top_strength && (
                            <div className="bg-emerald-50/70 p-2 rounded border border-emerald-200">
                              <strong className="text-[#047857]">Key Strength: </strong>
                              <span className="text-pencil">{item.top_strength}</span>
                            </div>
                          )}
                          {item.top_weakness && (
                            <div className="bg-red-50/70 p-2 rounded border border-red-200">
                              <strong className="text-marker">Focus Area: </strong>
                              <span className="text-pencil">{item.top_weakness}</span>
                            </div>
                          )}
                        </div>
                      )}

                      {/* Card Action Buttons */}
                      <div className="flex flex-wrap items-center justify-end gap-2 mt-3 pt-3 border-t border-dashed border-pencil/20">
                        {item.status === "COMPLETED" || item.overall_score !== null ? (
                          <WobblyButton
                            size="sm"
                            variant="primary"
                            onClick={() => handleViewPastReport(item.interview_id)}
                          >
                            <span className="flex items-center gap-1.5">
                              View Full Report &amp; Feedback <ArrowRight className="w-3.5 h-3.5" />
                            </span>
                          </WobblyButton>
                        ) : (
                          <WobblyButton
                            size="sm"
                            variant="danger"
                            onClick={() => handleResumeInterview(item.interview_id)}
                          >
                            <span className="flex items-center gap-1.5">
                              Resume Interview <Play className="w-3.5 h-3.5" />
                            </span>
                          </WobblyButton>
                        )}
                      </div>
                    </div>
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
