import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import ExamSession from './ExamSession';
import {
  BookOpen,
  Award,
  CheckCircle,
  Clock,
  ShieldCheck,
  Play,
  RefreshCw,
  X,
  Eye,
  TrendingUp,
  FileCheck,
  AlertTriangle
} from 'lucide-react';

export default function StudentDashboard() {
  const { authFetch } = useAuth();
  const [activeTab, setActiveTab] = useState('available');
  const [exams, setExams] = useState([]);
  const [mySubmissions, setMySubmissions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [activeSession, setActiveSession] = useState(null);
  const [submissionResult, setSubmissionResult] = useState(null);
  const [selectedSubDetail, setSelectedSubDetail] = useState(null);

  useEffect(() => {
    loadPublishedExams();
    loadMySubmissions();
  }, []);

  const loadPublishedExams = async () => {
    setLoading(true);
    try {
      const res = await authFetch('/api/exams');
      if (res.ok) setExams(await res.json());
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const loadMySubmissions = async () => {
    try {
      const res = await authFetch('/api/submissions/my');
      if (res.ok) setMySubmissions(await res.json());
    } catch (e) {
      console.error(e);
    }
  };

  const startExam = async (examId) => {
    try {
      const res = await authFetch('/api/submissions/start', {
        method: 'POST',
        body: JSON.stringify({ exam_id: examId })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Could not start exam session');
      setActiveSession(data);
    } catch (err) {
      alert(err.message);
    }
  };

  const handleFinishExam = (result) => {
    setActiveSession(null);
    setSubmissionResult(result);
    loadMySubmissions();
    loadPublishedExams();
  };

  const viewSubmissionDetail = async (subId) => {
    try {
      const res = await authFetch(`/api/submissions/${subId}`);
      if (res.ok) setSelectedSubDetail(await res.json());
    } catch (e) {
      console.error(e);
    }
  };

  if (activeSession) {
    return <ExamSession sessionData={activeSession} onFinishExam={handleFinishExam} />;
  }

  // Calculate high-level stats for widgets
  const totalCompleted = mySubmissions.length;
  const gradedList = mySubmissions.filter((s) => s.auto_score !== null);
  const avgScore = gradedList.length > 0
    ? Math.round((gradedList.reduce((acc, s) => acc + (s.auto_score / s.total_marks), 0) / gradedList.length) * 100)
    : 100;
  const lowRiskCount = mySubmissions.filter((s) => s.cheating_risk_level === 'LOW').length;
  const integrityScore = mySubmissions.length > 0
    ? Math.round((lowRiskCount / mySubmissions.length) * 100)
    : 99.4;

  return (
    <div className="container" style={{ maxWidth: '1180px' }}>
      {/* Top Header */}
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
            <Award size={13} />
            <span>Student Workspace</span>
          </div>
          <h1 style={{ fontSize: '2.1rem', fontWeight: 800 }}>Examinations & Performance</h1>
          <p className="subtitle" style={{ marginTop: '0.25rem' }}>
            Access encrypted assessments, complete personalized calibrations, and track real-time scorecards.
          </p>
        </div>

        <button
          onClick={() => {
            loadPublishedExams();
            loadMySubmissions();
          }}
          className="btn-secondary"
          style={{ fontSize: '0.82rem', padding: '0.55rem 1rem' }}
        >
          <RefreshCw size={14} className={loading ? 'spin' : ''} />
          <span>Sync Data</span>
        </button>
      </div>

      {/* Submission Success Alert Banner */}
      {submissionResult && (
        <div style={{
          backgroundColor: 'rgba(16, 185, 129, 0.12)',
          border: '1px solid var(--ft-primary-border)',
          borderRadius: '14px',
          padding: '1.25rem 1.5rem',
          marginBottom: '2rem',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          boxShadow: 'var(--ft-shadow-glow)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
            <div style={{
              width: '40px',
              height: '40px',
              borderRadius: '10px',
              backgroundColor: 'var(--ft-primary-muted)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--ft-primary-light)'
            }}>
              <CheckCircle size={22} />
            </div>
            <div>
              <h4 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#ffffff' }}>
                Examination Submitted & Decrypted Successfully
              </h4>
              <p style={{ fontSize: '0.82rem', color: 'var(--ft-primary-light)', marginTop: '0.1rem' }}>
                Auto-Graded Score: <strong>{submissionResult.auto_score} / {submissionResult.total_marks} Marks</strong> • Proctoring Integrity: {submissionResult.cheating_risk_level} Risk Level
              </p>
            </div>
          </div>
          <button
            onClick={() => setSubmissionResult(null)}
            className="btn-icon"
            style={{ width: '32px', height: '32px' }}
          >
            <X size={16} />
          </button>
        </div>
      )}

      {/* 4 Fintech KPI Metric Cards */}
      <div className="fintech-metric-grid">
        {/* Card 1: Available Exams */}
        <div className="fintech-stat-card">
          <div className="fintech-stat-header">
            <span className="fintech-stat-label">Available Exams</span>
            <div className="fintech-stat-icon-wrap">
              <BookOpen size={16} color="var(--ft-accent-cyan)" />
            </div>
          </div>
          <div>
            <div className="fintech-stat-value">{exams.length}</div>
            <div className="fintech-stat-subtext">
              <span className="trend-pill trend-pill-up">Active</span>
              <span>Ready for intake</span>
            </div>
          </div>
        </div>

        {/* Card 2: Completed Exams */}
        <div className="fintech-stat-card">
          <div className="fintech-stat-header">
            <span className="fintech-stat-label">Completed Exams</span>
            <div className="fintech-stat-icon-wrap">
              <FileCheck size={16} color="var(--ft-primary-light)" />
            </div>
          </div>
          <div>
            <div className="fintech-stat-value">{totalCompleted}</div>
            <div className="fintech-stat-subtext">
              <span className="trend-pill trend-pill-neutral">Recorded</span>
              <span>All submissions logged</span>
            </div>
          </div>
        </div>

        {/* Card 3: Average Score */}
        <div className="fintech-stat-card">
          <div className="fintech-stat-header">
            <span className="fintech-stat-label">Academic Score Avg</span>
            <div className="fintech-stat-icon-wrap">
              <TrendingUp size={16} color="#fbbf24" />
            </div>
          </div>
          <div>
            <div className="fintech-stat-value" style={{ color: 'var(--ft-primary-light)' }}>
              {avgScore}%
            </div>
            <div className="fintech-stat-subtext">
              <span className="trend-pill trend-pill-up">+4.2%</span>
              <span>Passing standard</span>
            </div>
          </div>
        </div>

        {/* Card 4: Integrity Rating */}
        <div className="fintech-stat-card">
          <div className="fintech-stat-header">
            <span className="fintech-stat-label">Proctoring Trust Index</span>
            <div className="fintech-stat-icon-wrap">
              <ShieldCheck size={16} color="var(--ft-primary-light)" />
            </div>
          </div>
          <div>
            <div className="fintech-stat-value">
              {integrityScore}%
            </div>
            <div className="fintech-stat-subtext">
              <span className="trend-pill trend-pill-up">Zero-Flagged</span>
              <span>Nominal posture</span>
            </div>
          </div>
        </div>
      </div>

      {/* Segmented Control Navigation Tabs */}
      <div className="fintech-tabs">
        <button
          onClick={() => setActiveTab('available')}
          className={`fintech-tab-item ${activeTab === 'available' ? 'active' : ''}`}
        >
          <BookOpen size={16} />
          <span>Available Assessments</span>
          <span className="fintech-tab-badge">{exams.length}</span>
        </button>

        <button
          onClick={() => setActiveTab('history')}
          className={`fintech-tab-item ${activeTab === 'history' ? 'active' : ''}`}
        >
          <Award size={16} />
          <span>Submissions & Scorecards</span>
          <span className="fintech-tab-badge">{mySubmissions.length}</span>
        </button>
      </div>

      {/* TAB 1: AVAILABLE EXAMS */}
      {activeTab === 'available' && (
        <div>
          {exams.length === 0 ? (
            <div className="fintech-card" style={{ textAlign: 'center', padding: '3.5rem 1.5rem' }}>
              <BookOpen size={44} color="var(--ft-text-dim)" style={{ marginBottom: '1rem' }} />
              <h3 style={{ fontSize: '1.15rem', color: '#ffffff', marginBottom: '0.4rem' }}>
                No Active Examinations Available
              </h3>
              <p style={{ fontSize: '0.85rem', color: 'var(--ft-text-secondary)', maxWidth: '420px', margin: '0 auto' }}>
                There are currently no published test papers assigned to your candidate profile. Check back when your course instructor releases the scheduled exam.
              </p>
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
                    {/* Card Top Pill */}
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
                        PAPER #{ex.id}
                      </span>
                      <span className="badge badge-success">
                        <span className="pulse-dot pulse-green" style={{ width: '5px', height: '5px' }} />
                        PUBLISHED
                      </span>
                    </div>

                    <h3 style={{ fontSize: '1.2rem', fontWeight: 700, marginBottom: '0.75rem', lineHeight: 1.3 }}>
                      {ex.title}
                    </h3>

                    {/* Meta Details Pills */}
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
                        {ex.duration_minutes} Minutes
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
                        <BookOpen size={13} color="var(--ft-accent-cyan)" />
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
                        AI Baseline Calibration
                      </span>
                    </div>
                  </div>

                  {/* Start Exam CTA */}
                  <button
                    onClick={() => startExam(ex.id)}
                    className="btn-primary"
                    style={{ width: '100%', padding: '0.75rem' }}
                  >
                    <Play size={16} />
                    <span>Launch Examination</span>
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* TAB 2: MY SUBMISSIONS & SCORES */}
      {activeTab === 'history' && (
        <div className="fintech-card" style={{ padding: '0.5rem' }}>
          <div className="fintech-table-wrapper">
            <table className="fintech-table">
              <thead>
                <tr>
                  <th>Examination</th>
                  <th>Submitted At</th>
                  <th>Auto-Grade Score</th>
                  <th>Proctoring Integrity</th>
                  <th style={{ textAlign: 'right' }}>Scorecard Action</th>
                </tr>
              </thead>
              <tbody>
                {mySubmissions.length === 0 ? (
                  <tr>
                    <td colSpan="5" style={{ padding: '3.5rem', textAlign: 'center', color: 'var(--ft-text-muted)' }}>
                      No examination history found. Complete an assessment to see your auto-graded scorecard.
                    </td>
                  </tr>
                ) : (
                  mySubmissions.map((sub) => (
                    <tr key={sub.id}>
                      <td style={{ fontWeight: 600, color: '#ffffff' }}>
                        <div>{sub.exam_title}</div>
                        <div style={{ fontSize: '0.72rem', color: 'var(--ft-text-muted)' }}>Session #{sub.id}</div>
                      </td>
                      <td style={{ color: 'var(--ft-text-secondary)', fontSize: '0.82rem' }}>
                        {sub.submitted_at ? new Date(sub.submitted_at).toLocaleString() : 'In Progress'}
                      </td>
                      <td>
                        <span style={{
                          fontFamily: 'var(--font-heading)',
                          fontSize: '1rem',
                          fontWeight: 700,
                          color: 'var(--ft-primary-light)'
                        }}>
                          {sub.auto_score !== null ? `${sub.auto_score} / ${sub.total_marks}` : '—'}
                        </span>
                        <span style={{ fontSize: '0.75rem', color: 'var(--ft-text-muted)', marginLeft: '0.25rem' }}>pts</span>
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
                          <ShieldCheck size={12} />
                          {sub.cheating_risk_level} RISK
                        </span>
                      </td>
                      <td style={{ textAlign: 'right' }}>
                        <button
                          onClick={() => viewSubmissionDetail(sub.id)}
                          className="btn-secondary"
                          style={{ fontSize: '0.78rem', padding: '0.35rem 0.75rem' }}
                        >
                          <Eye size={13} />
                          <span>View Scorecard</span>
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

      {/* Scorecard Modal */}
      {selectedSubDetail && (
        <div className="fintech-modal-overlay">
          <div className="fintech-modal-content" style={{ maxWidth: '780px' }}>
            <button
              onClick={() => setSelectedSubDetail(null)}
              className="btn-icon"
              style={{ position: 'absolute', top: '1.25rem', right: '1.25rem' }}
            >
              <X size={18} />
            </button>

            <div className="header-badge" style={{ marginBottom: '0.5rem' }}>
              Verified Candidate Scorecard
            </div>
            <h2 style={{ fontSize: '1.4rem', fontWeight: 800, marginBottom: '0.25rem' }}>
              {selectedSubDetail.exam_title}
            </h2>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '1rem',
              marginBottom: '1.75rem',
              flexWrap: 'wrap'
            }}>
              <span style={{ fontSize: '0.85rem', color: 'var(--ft-text-secondary)' }}>
                Final Score:{' '}
                <strong style={{ color: 'var(--ft-primary-light)', fontSize: '1rem' }}>
                  {selectedSubDetail.auto_score} / {selectedSubDetail.total_marks} pts
                </strong>
              </span>
              <span style={{ color: 'var(--ft-border-base)' }}>•</span>
              <span className={`badge ${selectedSubDetail.cheating_risk_level === 'HIGH' ? 'badge-error' : (selectedSubDetail.cheating_risk_level === 'MEDIUM' ? 'badge-warning' : 'badge-success')}`}>
                {selectedSubDetail.cheating_risk_level} Cheating Risk
              </span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
              {selectedSubDetail.questions_breakdown.map((qb, i) => (
                <div
                  key={i}
                  style={{
                    backgroundColor: 'rgba(255, 255, 255, 0.02)',
                    border: `1px solid ${qb.is_correct ? 'rgba(16, 185, 129, 0.3)' : 'rgba(244, 63, 94, 0.3)'}`,
                    borderRadius: '12px',
                    padding: '1.1rem'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.5rem' }}>
                    <span style={{ fontWeight: 700, color: '#ffffff', fontSize: '0.92rem' }}>
                      Q{i + 1}. {qb.question_text}
                    </span>
                    <span
                      className={`badge ${qb.is_correct ? 'badge-success' : 'badge-error'}`}
                      style={{ fontSize: '0.72rem' }}
                    >
                      {qb.marks_awarded} / {qb.max_marks} pts
                    </span>
                  </div>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem', fontSize: '0.82rem' }}>
                    <div style={{ color: qb.is_correct ? 'var(--ft-primary-light)' : '#fda4af' }}>
                      Your Answer: <strong>{qb.student_answer || '(No answer provided)'}</strong>
                    </div>
                    {qb.correct_answer && (
                      <div style={{ color: 'var(--ft-text-secondary)' }}>
                        Official Answer: <strong>{qb.correct_answer}</strong>
                      </div>
                    )}
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
