import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import {
  BookOpen,
  Plus,
  Activity,
  Eye,
  Trash2,
  CheckCircle,
  AlertTriangle,
  Radio,
  RefreshCw,
  X,
  ShieldAlert,
  Award,
  Clock,
  Layers,
  Sparkles,
  ChevronRight,
  ShieldCheck,
  Camera
} from 'lucide-react';

export default function FacultyDashboard() {
  const { authFetch } = useAuth();
  const [activeTab, setActiveTab] = useState('exams');
  const [exams, setExams] = useState([]);
  const [submissions, setSubmissions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [statusMessage, setStatusMessage] = useState(null);

  // Modals state
  const [showCreateExam, setShowCreateExam] = useState(false);
  const [newExam, setNewExam] = useState({
    title: '',
    duration_minutes: 30,
    start_time: new Date().toISOString().slice(0, 16),
    end_time: new Date(Date.now() + 7 * 86400000).toISOString().slice(0, 16)
  });

  const [selectedExamForQuestions, setSelectedExamForQuestions] = useState(null);
  const [questionsList, setQuestionsList] = useState([]);
  const [newQuestion, setNewQuestion] = useState({
    question_text: '',
    options: ['', '', '', ''],
    correct_answer: '',
    marks: 2
  });

  // Live Proctoring State
  const [selectedExamForLive, setSelectedExamForLive] = useState(null);
  const [liveAlerts, setLiveAlerts] = useState([]);
  const [wsConnected, setWsConnected] = useState(false);
  const wsRef = useRef(null);

  // Submissions drill-down
  const [selectedSubmissionDetail, setSelectedSubmissionDetail] = useState(null);

  useEffect(() => {
    loadExams();
  }, []);

  const loadExams = async () => {
    setLoading(true);
    try {
      const res = await authFetch('/api/exams');
      if (res.ok) {
        const data = await res.json();
        setExams(data);
        if (data.length > 0 && !selectedExamForLive) {
          setSelectedExamForLive(data[0].id);
        }
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const loadSubmissionsForExam = async (examId) => {
    try {
      const res = await authFetch(`/api/submissions/exam/${examId}`);
      if (res.ok) setSubmissions(await res.json());
    } catch (e) {
      console.error(e);
    }
  };

  // WebSocket Live Proctoring
  useEffect(() => {
    if (activeTab === 'proctor' && selectedExamForLive) {
      connectWebSocket(selectedExamForLive);
    }
    return () => {
      if (wsRef.current) wsRef.current.close();
    };
  }, [activeTab, selectedExamForLive]);

  const connectWebSocket = (examId) => {
    if (wsRef.current) wsRef.current.close();

    const host = window.location.hostname || 'localhost';
    const wsUrl = `ws://${host}:8000/api/proctoring/ws/${examId}`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      setWsConnected(true);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'PROCTORING_FLAG_ALERT') {
          setLiveAlerts((prev) => [data, ...prev.slice(0, 19)]);
        }
      } catch (e) {
        console.error(e);
      }
    };

    ws.onclose = () => {
      setWsConnected(false);
    };

    wsRef.current = ws;
  };

  const handleCreateExam = async (e) => {
    e.preventDefault();
    try {
      const res = await authFetch('/api/exams', {
        method: 'POST',
        body: JSON.stringify(newExam)
      });
      if (!res.ok) throw new Error('Failed to create exam');
      setShowCreateExam(false);
      setStatusMessage('Exam created successfully!');
      loadExams();
      setTimeout(() => setStatusMessage(null), 3000);
    } catch (err) {
      alert(err.message);
    }
  };

  const handleTogglePublish = async (examId) => {
    try {
      const res = await authFetch(`/api/exams/${examId}/publish`, { method: 'POST' });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Failed to toggle publish');
      }
      setStatusMessage('Exam status updated!');
      loadExams();
      setTimeout(() => setStatusMessage(null), 3000);
    } catch (err) {
      alert(err.message);
    }
  };

  const handleDeleteExam = async (examId) => {
    if (!window.confirm('Are you sure you want to delete this exam?')) return;
    try {
      const res = await authFetch(`/api/exams/${examId}`, { method: 'DELETE' });
      if (res.ok) {
        setStatusMessage('Exam deleted.');
        loadExams();
        setTimeout(() => setStatusMessage(null), 3000);
      }
    } catch (err) {
      alert('Delete failed');
    }
  };

  // Question Management
  const openQuestionsModal = async (exam) => {
    setSelectedExamForQuestions(exam);
    try {
      const res = await authFetch(`/api/exams/${exam.id}/questions`);
      if (res.ok) setQuestionsList(await res.json());
    } catch (e) {
      console.error(e);
    }
  };

  const handleAddQuestion = async (e) => {
    e.preventDefault();
    if (!newQuestion.correct_answer) {
      alert('Please select the correct answer among the options');
      return;
    }

    try {
      const res = await authFetch(`/api/exams/${selectedExamForQuestions.id}/questions`, {
        method: 'POST',
        body: JSON.stringify(newQuestion)
      });
      if (!res.ok) throw new Error('Failed to add question');

      setNewQuestion({
        question_text: '',
        options: ['', '', '', ''],
        correct_answer: '',
        marks: 2
      });
      openQuestionsModal(selectedExamForQuestions);
      loadExams();
      setStatusMessage('Question added and encrypted with AES-256!');
      setTimeout(() => setStatusMessage(null), 3000);
    } catch (err) {
      alert(err.message);
    }
  };

  const handleDeleteQuestion = async (questionId) => {
    try {
      const res = await authFetch(`/api/exams/${selectedExamForQuestions.id}/questions/${questionId}`, {
        method: 'DELETE'
      });
      if (res.ok) {
        openQuestionsModal(selectedExamForQuestions);
        loadExams();
      }
    } catch (e) {
      alert('Failed to delete question');
    }
  };

  const viewSubmissionDetail = async (subId) => {
    try {
      const res = await authFetch(`/api/submissions/${subId}`);
      if (res.ok) setSelectedSubmissionDetail(await res.json());
    } catch (e) {
      console.error(e);
    }
  };

  const publishedCount = exams.filter((e) => e.status === 'PUBLISHED').length;

  return (
    <div className="container" style={{ maxWidth: '1180px' }}>
      {/* Header */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'flex-start',
        marginBottom: '2rem',
        flexWrap: 'wrap',
        gap: '1rem'
      }}>
        <div>
          <div className="header-badge">
            <BookOpen size={13} />
            <span>Faculty & Examiner Workspace</span>
          </div>
          <h1 style={{ fontSize: '2.1rem', fontWeight: 800 }}>Examinations & Live AI Proctoring</h1>
          <p className="subtitle" style={{ marginTop: '0.25rem' }}>
            Author encrypted examinations, monitor live sessions via WebSockets, and inspect auto-graded scorecards.
          </p>
        </div>

        <button
          onClick={() => setShowCreateExam(true)}
          className="btn-primary"
          style={{ fontSize: '0.9rem', padding: '0.7rem 1.4rem' }}
        >
          <Plus size={16} />
          <span>Author New Exam</span>
        </button>
      </div>

      {statusMessage && (
        <div style={{
          backgroundColor: 'rgba(16, 185, 129, 0.12)',
          border: '1px solid var(--ft-primary-border)',
          borderRadius: '10px',
          padding: '0.85rem 1.25rem',
          marginBottom: '1.5rem',
          color: 'var(--ft-primary-light)',
          fontSize: '0.88rem',
          fontWeight: 600,
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem'
        }}>
          <CheckCircle size={16} />
          <span>{statusMessage}</span>
        </div>
      )}

      {/* KPI Metric Cards */}
      <div className="fintech-metric-grid">
        <div className="fintech-stat-card">
          <div className="fintech-stat-header">
            <span className="fintech-stat-label">Total Examinations</span>
            <div className="fintech-stat-icon-wrap">
              <BookOpen size={16} color="var(--ft-accent-cyan)" />
            </div>
          </div>
          <div>
            <div className="fintech-stat-value">{exams.length}</div>
            <div className="fintech-stat-subtext">
              <span className="trend-pill trend-pill-up">{publishedCount} Published</span>
              <span>In portal catalogue</span>
            </div>
          </div>
        </div>

        <div className="fintech-stat-card">
          <div className="fintech-stat-header">
            <span className="fintech-stat-label">AI Proctoring Stream</span>
            <div className="fintech-stat-icon-wrap">
              <Radio size={16} color="var(--ft-primary-light)" />
            </div>
          </div>
          <div>
            <div className="fintech-stat-value" style={{ color: wsConnected ? 'var(--ft-primary-light)' : 'var(--ft-text-secondary)' }}>
              {wsConnected ? 'Connected' : 'Standby'}
            </div>
            <div className="fintech-stat-subtext">
              <span className={`trend-pill ${wsConnected ? 'trend-pill-up' : 'trend-pill-neutral'}`}>
                {wsConnected ? 'WebSocket Live' : 'Idle'}
              </span>
              <span>Real-time channel</span>
            </div>
          </div>
        </div>

        <div className="fintech-stat-card">
          <div className="fintech-stat-header">
            <span className="fintech-stat-label">Flagged Live Events</span>
            <div className="fintech-stat-icon-wrap">
              <ShieldAlert size={16} color="#fda4af" />
            </div>
          </div>
          <div>
            <div className="fintech-stat-value" style={{ color: liveAlerts.length > 0 ? '#fda4af' : 'var(--ft-text-primary)' }}>
              {liveAlerts.length}
            </div>
            <div className="fintech-stat-subtext">
              <span className="trend-pill trend-pill-down">≥60% Confidence</span>
              <span>Snapshot alerts</span>
            </div>
          </div>
        </div>

        <div className="fintech-stat-card">
          <div className="fintech-stat-header">
            <span className="fintech-stat-label">Encryption Level</span>
            <div className="fintech-stat-icon-wrap">
              <ShieldCheck size={16} color="var(--ft-primary-light)" />
            </div>
          </div>
          <div>
            <div className="fintech-stat-value">AES-256</div>
            <div className="fintech-stat-subtext">
              <span className="trend-pill trend-pill-up">GCM Mode</span>
              <span>Encrypted at rest</span>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="fintech-tabs">
        <button
          onClick={() => setActiveTab('exams')}
          className={`fintech-tab-item ${activeTab === 'exams' ? 'active' : ''}`}
        >
          <BookOpen size={16} />
          <span>My Examinations</span>
          <span className="fintech-tab-badge">{exams.length}</span>
        </button>

        <button
          onClick={() => setActiveTab('proctor')}
          className={`fintech-tab-item ${activeTab === 'proctor' ? 'active' : ''}`}
        >
          <Radio size={16} color="var(--ft-primary-light)" />
          <span>Live AI Proctoring Feed</span>
          {liveAlerts.length > 0 && (
            <span className="fintech-tab-badge" style={{ backgroundColor: 'rgba(244, 63, 94, 0.25)', color: '#fda4af' }}>
              {liveAlerts.length}
            </span>
          )}
        </button>

        <button
          onClick={() => {
            setActiveTab('submissions');
            if (exams.length > 0) loadSubmissionsForExam(exams[0].id);
          }}
          className={`fintech-tab-item ${activeTab === 'submissions' ? 'active' : ''}`}
        >
          <Award size={16} />
          <span>Submissions & Grading</span>
        </button>
      </div>

      {/* TAB 1: MY EXAMINATIONS */}
      {activeTab === 'exams' && (
        <div>
          {exams.length === 0 ? (
            <div className="fintech-card" style={{ textAlign: 'center', padding: '3.5rem 1.5rem' }}>
              <BookOpen size={44} color="var(--ft-text-dim)" style={{ marginBottom: '1rem' }} />
              <h3 style={{ fontSize: '1.15rem', color: '#ffffff', marginBottom: '0.4rem' }}>
                No Examinations Authored Yet
              </h3>
              <p style={{ fontSize: '0.85rem', color: 'var(--ft-text-secondary)', maxWidth: '420px', margin: '0 auto 1.5rem' }}>
                Get started by clicking the "Author New Exam" button above to configure your test schedule and encrypted question paper.
              </p>
              <button onClick={() => setShowCreateExam(true)} className="btn-primary">
                <Plus size={16} /> Author First Exam
              </button>
            </div>
          ) : (
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))',
              gap: '1.25rem'
            }}>
              {exams.map((ex) => (
                <div
                  key={ex.id}
                  className="fintech-card"
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'space-between',
                    gap: '1.25rem'
                  }}
                >
                  <div>
                    <div style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      marginBottom: '0.85rem'
                    }}>
                      <span style={{
                        fontSize: '0.72rem',
                        fontWeight: 700,
                        color: 'var(--ft-text-muted)',
                        letterSpacing: '0.06em',
                        textTransform: 'uppercase'
                      }}>
                        EXAM #{ex.id}
                      </span>
                      <span className={`badge ${ex.status === 'PUBLISHED' ? 'badge-success' : 'badge-warning'}`}>
                        {ex.status}
                      </span>
                    </div>

                    <h3 style={{ fontSize: '1.2rem', fontWeight: 700, marginBottom: '0.75rem', lineHeight: 1.3 }}>
                      {ex.title}
                    </h3>

                    <div style={{
                      display: 'flex',
                      flexWrap: 'wrap',
                      gap: '0.45rem',
                      marginBottom: '1rem'
                    }}>
                      <span style={{
                        fontSize: '0.75rem',
                        padding: '0.3rem 0.65rem',
                        borderRadius: '6px',
                        backgroundColor: 'rgba(255, 255, 255, 0.04)',
                        border: '1px solid var(--ft-border-subtle)',
                        color: 'var(--ft-text-secondary)',
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '0.35rem'
                      }}>
                        <Clock size={13} color="var(--ft-primary-light)" />
                        {ex.duration_minutes} Mins
                      </span>

                      <span style={{
                        fontSize: '0.75rem',
                        padding: '0.3rem 0.65rem',
                        borderRadius: '6px',
                        backgroundColor: 'rgba(255, 255, 255, 0.04)',
                        border: '1px solid var(--ft-border-subtle)',
                        color: 'var(--ft-text-secondary)',
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '0.35rem'
                      }}>
                        <Layers size={13} color="var(--ft-accent-cyan)" />
                        {ex.total_questions} Questions ({ex.total_marks} Marks)
                      </span>

                      <span style={{
                        fontSize: '0.75rem',
                        padding: '0.3rem 0.65rem',
                        borderRadius: '6px',
                        backgroundColor: 'rgba(255, 255, 255, 0.04)',
                        border: '1px solid var(--ft-border-subtle)',
                        color: 'var(--ft-text-secondary)',
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '0.35rem'
                      }}>
                        <ShieldCheck size={13} color="#fbbf24" />
                        AES-256 Vault
                      </span>
                    </div>
                  </div>

                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                    paddingTop: '0.85rem',
                    borderTop: '1px solid var(--ft-border-subtle)'
                  }}>
                    <button
                      onClick={() => openQuestionsModal(ex)}
                      className="btn-secondary"
                      style={{ fontSize: '0.8rem', padding: '0.45rem 0.75rem', flex: 1 }}
                    >
                      <span>Questions ({ex.total_questions})</span>
                    </button>

                    <button
                      onClick={() => handleTogglePublish(ex.id)}
                      className="btn-secondary"
                      style={{
                        fontSize: '0.8rem',
                        padding: '0.45rem 0.75rem',
                        color: ex.status === 'PUBLISHED' ? '#fbbf24' : 'var(--ft-primary-light)',
                        borderColor: ex.status === 'PUBLISHED' ? 'rgba(245, 158, 11, 0.3)' : 'var(--ft-primary-border)'
                      }}
                    >
                      {ex.status === 'PUBLISHED' ? 'Unpublish' : 'Publish'}
                    </button>

                    <button
                      onClick={() => handleDeleteExam(ex.id)}
                      className="btn-icon"
                      style={{ color: '#fda4af' }}
                      title="Delete Exam"
                    >
                      <Trash2 size={15} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* TAB 2: LIVE PROCTORING MONITOR */}
      {activeTab === 'proctor' && (
        <div className="fintech-card">
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '1.5rem',
            flexWrap: 'wrap',
            gap: '1rem'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
              <div style={{
                width: '36px',
                height: '36px',
                borderRadius: '8px',
                backgroundColor: 'var(--ft-primary-muted)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'var(--ft-primary-light)'
              }}>
                <Radio size={18} />
              </div>
              <div>
                <h3 style={{ fontSize: '1.15rem', fontWeight: 700 }}>Real-Time Live Proctoring Feed</h3>
                <div style={{ fontSize: '0.75rem', color: 'var(--ft-text-muted)' }}>
                  WebSocket Channel • Instantaneous YOLOv8 + Resemblyzer flag broadcasts
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <span className={`badge ${wsConnected ? 'badge-success' : 'badge-error'}`}>
                <span className={`pulse-dot ${wsConnected ? 'pulse-green' : 'pulse-red'}`} />
                {wsConnected ? 'WS Feed Active' : 'Connecting...'}
              </span>

              <select
                value={selectedExamForLive || ''}
                onChange={(e) => setSelectedExamForLive(Number(e.target.value))}
                className="fintech-input"
                style={{ width: 'auto', padding: '0.45rem 0.85rem', fontSize: '0.82rem' }}
              >
                {exams.map((ex) => (
                  <option key={ex.id} value={ex.id}>
                    #{ex.id} {ex.title}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {liveAlerts.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '4rem 1.5rem', color: 'var(--ft-text-secondary)' }}>
              <div style={{
                width: '64px',
                height: '64px',
                borderRadius: '50%',
                backgroundColor: 'rgba(16, 185, 129, 0.08)',
                border: '1px solid var(--ft-primary-border)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                margin: '0 auto 1.25rem',
                color: 'var(--ft-primary-light)'
              }}>
                <ShieldAlert size={28} />
              </div>
              <h3 style={{ fontSize: '1.15rem', color: '#ffffff', marginBottom: '0.4rem' }}>
                Monitoring Active Candidate Sessions...
              </h3>
              <p style={{ fontSize: '0.85rem', maxWidth: '480px', margin: '0 auto', color: 'var(--ft-text-muted)' }}>
                When candidates take an exam with webcam telemetry enabled, any behaviour exceeding the 60% suspicion threshold will broadcast instant snapshots and modality flags here.
              </p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
              {liveAlerts.map((alert, idx) => (
                <div
                  key={idx}
                  style={{
                    backgroundColor: 'rgba(244, 63, 94, 0.04)',
                    border: '1px solid rgba(244, 63, 94, 0.3)',
                    borderRadius: '12px',
                    padding: '1rem 1.25rem',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    flexWrap: 'wrap',
                    gap: '1rem'
                  }}
                >
                  <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
                    {alert.snapshot && (
                      <img
                        src={alert.snapshot.startsWith('data:') ? alert.snapshot : `data:image/jpeg;base64,${alert.snapshot}`}
                        alt="Webcam Alert Snapshot"
                        style={{
                          width: '90px',
                          height: '68px',
                          objectFit: 'cover',
                          borderRadius: '8px',
                          border: '1px solid rgba(244, 63, 94, 0.4)'
                        }}
                      />
                    )}
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.2rem' }}>
                        <span style={{ fontWeight: 700, fontSize: '0.95rem', color: '#ffffff' }}>
                          {alert.student_name}
                        </span>
                        <span className="badge badge-error" style={{ fontSize: '0.72rem' }}>
                          Risk: {Math.round(alert.cheating_probability * 100)}%
                        </span>
                      </div>
                      <div style={{ fontSize: '0.78rem', color: 'var(--ft-text-muted)', marginBottom: '0.45rem' }}>
                        {alert.student_email}
                      </div>

                      <div style={{ display: 'flex', gap: '0.35rem', flexWrap: 'wrap' }}>
                        {alert.flags.map((f, i) => (
                          <span
                            key={i}
                            style={{
                              fontSize: '0.7rem',
                              backgroundColor: 'rgba(244, 63, 94, 0.15)',
                              color: '#fda4af',
                              padding: '0.15rem 0.5rem',
                              borderRadius: '4px',
                              border: '1px solid rgba(244, 63, 94, 0.3)'
                            }}
                          >
                            ⚠️ {f}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>

                  <span style={{ fontSize: '0.75rem', color: 'var(--ft-text-muted)', fontFamily: 'var(--font-mono)' }}>
                    {alert.timestamp}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* TAB 3: SUBMISSIONS & GRADING */}
      {activeTab === 'submissions' && (
        <div className="fintech-card" style={{ padding: '1rem' }}>
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '1.25rem',
            flexWrap: 'wrap',
            gap: '1rem',
            padding: '0 0.5rem'
          }}>
            <div>
              <h3 style={{ fontSize: '1.15rem', fontWeight: 700 }}>Candidate Submissions & Auto-Graded Scores</h3>
              <div style={{ fontSize: '0.75rem', color: 'var(--ft-text-muted)' }}>
                Inspect objective question answers, awarded marks, and multimodal proctoring flags.
              </div>
            </div>

            {exams.length > 0 && (
              <select
                onChange={(e) => loadSubmissionsForExam(Number(e.target.value))}
                className="fintech-input"
                style={{ width: 'auto', padding: '0.45rem 0.85rem', fontSize: '0.82rem' }}
              >
                {exams.map((ex) => (
                  <option key={ex.id} value={ex.id}>
                    #{ex.id} {ex.title}
                  </option>
                ))}
              </select>
            )}
          </div>

          <div className="fintech-table-wrapper">
            <table className="fintech-table">
              <thead>
                <tr>
                  <th>Candidate</th>
                  <th>Auto-Score</th>
                  <th>Integrity Level</th>
                  <th>Status</th>
                  <th style={{ textAlign: 'right' }}>Scorecard Review</th>
                </tr>
              </thead>
              <tbody>
                {submissions.length === 0 ? (
                  <tr>
                    <td colSpan="5" style={{ padding: '3.5rem', textAlign: 'center', color: 'var(--ft-text-muted)' }}>
                      No student submissions recorded for this examination yet.
                    </td>
                  </tr>
                ) : (
                  submissions.map((sub) => (
                    <tr key={sub.id}>
                      <td>
                        <div style={{ fontWeight: 600, color: '#ffffff' }}>{sub.student_name}</div>
                        <div style={{ fontSize: '0.72rem', color: 'var(--ft-text-muted)' }}>{sub.student_email}</div>
                      </td>
                      <td>
                        <span style={{
                          fontFamily: 'var(--font-heading)',
                          fontSize: '1rem',
                          fontWeight: 700,
                          color: 'var(--ft-primary-light)'
                        }}>
                          {sub.auto_score !== null ? `${sub.auto_score} / ${sub.total_marks}` : 'Pending'}
                        </span>
                        <span style={{ fontSize: '0.75rem', color: 'var(--ft-text-muted)', marginLeft: '0.2rem' }}>pts</span>
                      </td>
                      <td>
                        <span
                          className={`badge ${
                            sub.cheating_risk_level === 'HIGH'
                              ? 'badge-error'
                              : sub.cheating_risk_level === 'MEDIUM'
                              ? 'badge-warning'
                              : 'badge-success'
                          }`}
                        >
                          {sub.cheating_risk_level} RISK ({sub.flagged_events_count} flags)
                        </span>
                      </td>
                      <td>
                        <span className="badge badge-neutral">{sub.status}</span>
                      </td>
                      <td style={{ textAlign: 'right' }}>
                        <button
                          onClick={() => viewSubmissionDetail(sub.id)}
                          className="btn-secondary"
                          style={{ fontSize: '0.78rem', padding: '0.35rem 0.75rem' }}
                        >
                          <Eye size={13} />
                          <span>Review Answers</span>
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* MODAL 1: Author New Exam Modal */}
      {showCreateExam && (
        <div className="fintech-modal-overlay">
          <div className="fintech-modal-content" style={{ maxWidth: '480px' }}>
            <button
              onClick={() => setShowCreateExam(false)}
              className="btn-icon"
              style={{ position: 'absolute', top: '1.25rem', right: '1.25rem' }}
            >
              <X size={18} />
            </button>

            <div className="header-badge" style={{ marginBottom: '0.5rem' }}>
              New Examination Paper
            </div>
            <h3 style={{ fontSize: '1.35rem', fontWeight: 800, marginBottom: '0.25rem' }}>
              Author Examination
            </h3>
            <p className="subtitle" style={{ fontSize: '0.82rem', marginBottom: '1.5rem', marginTop: 0 }}>
              Specify title, duration, and test validity window. Questions are encrypted with AES-256.
            </p>

            <form onSubmit={handleCreateExam} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div>
                <label className="fintech-label">Exam Title</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Distributed Systems Final Examination"
                  value={newExam.title}
                  onChange={(e) => setNewExam({ ...newExam, title: e.target.value })}
                  className="fintech-input"
                />
              </div>

              <div>
                <label className="fintech-label">Duration (Minutes)</label>
                <input
                  type="number"
                  required
                  min="5"
                  max="180"
                  value={newExam.duration_minutes}
                  onChange={(e) => setNewExam({ ...newExam, duration_minutes: Number(e.target.value) })}
                  className="fintech-input"
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                <div>
                  <label className="fintech-label">Window Opens</label>
                  <input
                    type="datetime-local"
                    value={newExam.start_time}
                    onChange={(e) => setNewExam({ ...newExam, start_time: e.target.value })}
                    className="fintech-input"
                  />
                </div>
                <div>
                  <label className="fintech-label">Window Closes</label>
                  <input
                    type="datetime-local"
                    value={newExam.end_time}
                    onChange={(e) => setNewExam({ ...newExam, end_time: e.target.value })}
                    className="fintech-input"
                  />
                </div>
              </div>

              <div style={{ display: 'flex', gap: '0.75rem', marginTop: '0.75rem' }}>
                <button type="submit" className="btn-primary" style={{ flex: 1, padding: '0.75rem' }}>
                  Create Paper
                </button>
                <button
                  type="button"
                  onClick={() => setShowCreateExam(false)}
                  className="btn-secondary"
                  style={{ flex: 1 }}
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL 2: Question Paper Builder Modal */}
      {selectedExamForQuestions && (
        <div className="fintech-modal-overlay">
          <div className="fintech-modal-content" style={{ maxWidth: '780px' }}>
            <button
              onClick={() => setSelectedExamForQuestions(null)}
              className="btn-icon"
              style={{ position: 'absolute', top: '1.25rem', right: '1.25rem' }}
            >
              <X size={18} />
            </button>

            <div className="header-badge" style={{ marginBottom: '0.5rem' }}>
              AES-256 Question Paper Vault
            </div>
            <h2 style={{ fontSize: '1.35rem', fontWeight: 800, marginBottom: '0.2rem' }}>
              {selectedExamForQuestions.title}
            </h2>
            <p style={{ fontSize: '0.82rem', color: 'var(--ft-text-muted)', marginBottom: '1.5rem' }}>
              Question strings and answer keys are encrypted with authenticated AES-256 at rest.
            </p>

            {/* Existing Questions List */}
            <div style={{ marginBottom: '2rem' }}>
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '0.75rem'
              }}>
                <h4 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--ft-primary-light)' }}>
                  Current Questions ({questionsList.length})
                </h4>
              </div>

              {questionsList.length === 0 ? (
                <div style={{
                  padding: '1.5rem',
                  borderRadius: '10px',
                  backgroundColor: 'rgba(255, 255, 255, 0.02)',
                  border: '1px solid var(--ft-border-subtle)',
                  textAlign: 'center',
                  color: 'var(--ft-text-muted)',
                  fontSize: '0.85rem'
                }}>
                  No questions added to this paper yet. Use the form below to add questions.
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                  {questionsList.map((q, idx) => (
                    <div
                      key={q.id}
                      style={{
                        backgroundColor: 'rgba(255, 255, 255, 0.02)',
                        border: '1px solid var(--ft-border-subtle)',
                        borderRadius: '10px',
                        padding: '1rem'
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                        <span style={{ fontWeight: 700, fontSize: '0.9rem', color: '#ffffff' }}>
                          Q{idx + 1}. {q.question_text}
                        </span>
                        <button
                          onClick={() => handleDeleteQuestion(q.id)}
                          className="btn-icon"
                          style={{ width: '28px', height: '28px', color: '#fda4af' }}
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>

                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.4rem', marginTop: '0.6rem', fontSize: '0.8rem' }}>
                        {q.options.map((opt, oIdx) => (
                          <div
                            key={oIdx}
                            style={{
                              padding: '0.4rem 0.65rem',
                              borderRadius: '6px',
                              backgroundColor: opt === q.correct_answer ? 'rgba(16, 185, 129, 0.15)' : 'rgba(0, 0, 0, 0.3)',
                              color: opt === q.correct_answer ? 'var(--ft-primary-light)' : 'var(--ft-text-secondary)',
                              border: opt === q.correct_answer ? '1px solid var(--ft-primary-border)' : '1px solid var(--ft-border-subtle)',
                              fontWeight: opt === q.correct_answer ? 700 : 400
                            }}
                          >
                            {opt} {opt === q.correct_answer && '✓ (Correct)'}
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Add Question Form */}
            <form
              onSubmit={handleAddQuestion}
              style={{
                backgroundColor: 'rgba(255, 255, 255, 0.02)',
                padding: '1.25rem',
                borderRadius: '12px',
                border: '1px solid var(--ft-border-subtle)'
              }}
            >
              <h4 style={{ fontSize: '0.95rem', fontWeight: 700, marginBottom: '0.85rem' }}>
                Add New Objective Question
              </h4>

              <div style={{ marginBottom: '0.85rem' }}>
                <label className="fintech-label">Question Text</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Which consensus algorithm is used by Raft?"
                  value={newQuestion.question_text}
                  onChange={(e) => setNewQuestion({ ...newQuestion, question_text: e.target.value })}
                  className="fintech-input"
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.6rem', marginBottom: '0.85rem' }}>
                {newQuestion.options.map((opt, idx) => (
                  <div key={idx}>
                    <label className="fintech-label">Option {String.fromCharCode(65 + idx)}</label>
                    <input
                      type="text"
                      required
                      placeholder={`Choice ${String.fromCharCode(65 + idx)}`}
                      value={opt}
                      onChange={(e) => {
                        const updated = [...newQuestion.options];
                        updated[idx] = e.target.value;
                        setNewQuestion({ ...newQuestion, options: updated });
                      }}
                      className="fintech-input"
                    />
                  </div>
                ))}
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '0.75rem', marginBottom: '1rem' }}>
                <div>
                  <label className="fintech-label">Select Correct Answer</label>
                  <select
                    value={newQuestion.correct_answer}
                    onChange={(e) => setNewQuestion({ ...newQuestion, correct_answer: e.target.value })}
                    className="fintech-input"
                    required
                  >
                    <option value="">-- Choose correct option --</option>
                    {newQuestion.options.filter(Boolean).map((opt, idx) => (
                      <option key={idx} value={opt}>
                        {opt}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="fintech-label">Marks</label>
                  <input
                    type="number"
                    min="1"
                    max="10"
                    value={newQuestion.marks}
                    onChange={(e) => setNewQuestion({ ...newQuestion, marks: Number(e.target.value) })}
                    className="fintech-input"
                  />
                </div>
              </div>

              <button type="submit" className="btn-primary" style={{ width: '100%', padding: '0.75rem' }}>
                <Plus size={16} /> Encrypt & Add Question
              </button>
            </form>
          </div>
        </div>
      )}

      {/* MODAL 3: Detailed Submission Review */}
      {selectedSubmissionDetail && (
        <div className="fintech-modal-overlay">
          <div className="fintech-modal-content" style={{ maxWidth: '780px' }}>
            <button
              onClick={() => setSelectedSubmissionDetail(null)}
              className="btn-icon"
              style={{ position: 'absolute', top: '1.25rem', right: '1.25rem' }}
            >
              <X size={18} />
            </button>

            <div className="header-badge" style={{ marginBottom: '0.5rem' }}>
              Submission Audit & Scorecard
            </div>
            <h2 style={{ fontSize: '1.4rem', fontWeight: 800, marginBottom: '0.2rem' }}>
              {selectedSubmissionDetail.exam_title}
            </h2>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '1rem',
              marginBottom: '1.5rem',
              flexWrap: 'wrap'
            }}>
              <span style={{ fontSize: '0.85rem', color: 'var(--ft-text-secondary)' }}>
                Candidate: <strong style={{ color: '#ffffff' }}>{selectedSubmissionDetail.student_name}</strong> ({selectedSubmissionDetail.student_email})
              </span>
              <span style={{ color: 'var(--ft-border-base)' }}>•</span>
              <span style={{ fontSize: '0.85rem', color: 'var(--ft-primary-light)', fontWeight: 700 }}>
                Score: {selectedSubmissionDetail.auto_score} / {selectedSubmissionDetail.total_marks} pts
              </span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {selectedSubmissionDetail.questions_breakdown.map((qb, i) => (
                <div
                  key={i}
                  style={{
                    backgroundColor: 'rgba(255, 255, 255, 0.02)',
                    border: `1px solid ${qb.is_correct ? 'rgba(16, 185, 129, 0.3)' : 'rgba(244, 63, 94, 0.3)'}`,
                    borderRadius: '10px',
                    padding: '1rem'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.4rem' }}>
                    <span style={{ fontWeight: 700, color: '#ffffff', fontSize: '0.9rem' }}>
                      Q{i + 1}. {qb.question_text}
                    </span>
                    <span className={`badge ${qb.is_correct ? 'badge-success' : 'badge-error'}`} style={{ fontSize: '0.7rem' }}>
                      {qb.marks_awarded} / {qb.max_marks} pts
                    </span>
                  </div>
                  <div style={{ fontSize: '0.8rem', display: 'flex', flexDirection: 'column', gap: '0.2rem' }}>
                    <span style={{ color: qb.is_correct ? 'var(--ft-primary-light)' : '#fda4af' }}>
                      Candidate Answer: <strong>{qb.student_answer || '(Blank)'}</strong>
                    </span>
                    <span style={{ color: 'var(--ft-text-muted)' }}>
                      Correct Answer: <strong>{qb.correct_answer}</strong>
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
