import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import {
  Clock,
  ShieldCheck,
  ShieldAlert,
  ChevronLeft,
  ChevronRight,
  CheckCircle,
  Save,
  AlertCircle,
  Camera,
  Mic,
  MicOff,
  Video,
  X,
  Layers,
  Sparkles
} from 'lucide-react';

export default function ExamSession({ sessionData, onFinishExam }) {
  const { authFetch } = useAuth();
  const [currentQIndex, setCurrentQIndex] = useState(0);
  const [answers, setAnswers] = useState(sessionData.saved_answers || {});
  const [timeLeft, setTimeLeft] = useState(sessionData.duration_minutes * 60);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [lastAutosave, setLastAutosave] = useState(null);
  const [showSubmitModal, setShowSubmitModal] = useState(false);

  // AI Proctoring Webcam & Analysis
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const [proctorStatus, setProctorStatus] = useState({ active: false, suspicious: false, flags: [] });
  const [cameraError, setCameraError] = useState(null);

  const questions = sessionData.questions || [];
  const currentQ = questions[currentQIndex];

  // Personalized Multi-Modal Calibration State
  const [calibrationPhase, setCalibrationPhase] = useState(true);
  const [calibrationProgress, setCalibrationProgress] = useState(0);
  const [verificationPhrase, setVerificationPhrase] = useState('');
  const [isRecordingAudio, setIsRecordingAudio] = useState(false);
  const [audioEnrolled, setAudioEnrolled] = useState(false);
  const [micDenied, setMicDenied] = useState(false);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  // 1. Fetch Verification Phrase on Load
  useEffect(() => {
    authFetch('/api/proctoring/verification-phrase')
      .then((res) => res.json())
      .then((data) => {
        if (data && data.phrase) setVerificationPhrase(data.phrase);
      })
      .catch(() => {
        setVerificationPhrase('I verify that I am sitting at my desk taking this examination honestly.');
      });
  }, []);

  // 2. Initialize Media Stream (Video & Audio)
  useEffect(() => {
    let stream = null;
    navigator.mediaDevices
      ?.getUserMedia({ video: { width: 640, height: 480 }, audio: true })
      .then((s) => {
        stream = s;
        if (videoRef.current) {
          videoRef.current.srcObject = s;
          setProctorStatus((prev) => ({ ...prev, active: true }));
        }
      })
      .catch(() => {
        // Fallback to video-only if mic denied
        navigator.mediaDevices
          ?.getUserMedia({ video: { width: 640, height: 480 } })
          .then((s) => {
            stream = s;
            if (videoRef.current) {
              videoRef.current.srcObject = s;
              setProctorStatus((prev) => ({ ...prev, active: true }));
            }
            setMicDenied(true);
          })
          .catch(() => {
            setCameraError('Webcam access is mandatory for AI proctoring compliance.');
          });
      });

    return () => {
      if (stream) {
        stream.getTracks().forEach((track) => track.stop());
      }
    };
  }, []);

  // 3. Calibration Video Stream Accumulator
  useEffect(() => {
    if (!calibrationPhase) return;
    const interval = setInterval(async () => {
      if (!videoRef.current || !canvasRef.current) return;
      const video = videoRef.current;
      const canvas = canvasRef.current;
      if (video.videoWidth === 0) return;

      canvas.width = 640;
      canvas.height = 480;
      const ctx = canvas.getContext('2d');
      ctx.drawImage(video, 0, 0, 640, 480);
      const frameBase64 = canvas.toDataURL('image/jpeg', 0.8);

      try {
        const res = await authFetch('/api/proctoring/calibrate-video', {
          method: 'POST',
          body: JSON.stringify({
            submission_id: sessionData.submission_id,
            frame_base64: frameBase64
          })
        });
        if (res.ok) {
          const data = await res.json();
          const progressPct = Math.min(100, Math.round((data.samples_count / 30) * 100));
          setCalibrationProgress(progressPct);
        }
      } catch (e) {
        console.error('Calibration sample error:', e);
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [calibrationPhase, sessionData.submission_id]);

  // 4. Audio Phrase Recording Handler
  const startRecordingPhrase = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioChunksRef.current = [];
      const recorder = new MediaRecorder(stream);
      mediaRecorderRef.current = recorder;

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data);
      };

      recorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        const reader = new FileReader();
        reader.readAsDataURL(audioBlob);
        reader.onloadend = async () => {
          const base64Audio = reader.result.split(',')[1];
          try {
            const res = await authFetch('/api/proctoring/calibrate-audio', {
              method: 'POST',
              body: JSON.stringify({
                submission_id: sessionData.submission_id,
                audio_base64: base64Audio,
                phrase_text: verificationPhrase
              })
            });
            if (res.ok) {
              setAudioEnrolled(true);
            }
          } catch (err) {
            console.error('Audio calibration failed:', err);
          }
        };
      };

      recorder.start();
      setIsRecordingAudio(true);
    } catch (err) {
      setMicDenied(true);
    }
  };

  const stopRecordingPhrase = () => {
    if (mediaRecorderRef.current && isRecordingAudio) {
      mediaRecorderRef.current.stop();
      setIsRecordingAudio(false);
    }
  };

  // 5. Periodic AI Frame Analysis during Exam
  useEffect(() => {
    if (calibrationPhase) return;
    const interval = setInterval(async () => {
      captureAndSendFrame();
    }, 4000);
    return () => clearInterval(interval);
  }, [calibrationPhase, sessionData.submission_id, micDenied]);

  const captureAndSendFrame = async () => {
    if (!videoRef.current || !canvasRef.current) return;
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (video.videoWidth === 0) return;

    canvas.width = 640;
    canvas.height = 480;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, 640, 480);
    const frameBase64 = canvas.toDataURL('image/jpeg', 0.75);

    try {
      const res = await authFetch('/api/proctoring/analyze-multimodal', {
        method: 'POST',
        body: JSON.stringify({
          submission_id: sessionData.submission_id,
          frame_base64: frameBase64,
          mode: micDenied ? 'video_only' : 'fused'
        })
      });

      if (res.ok) {
        const data = await res.json();
        setProctorStatus({
          active: true,
          suspicious: data.is_suspicious,
          flags: data.flags,
          cheating_prob: data.cheating_probability,
          parallel_comparison: data.parallel_comparison
        });
      }
    } catch (e) {
      console.error('Proctoring multimodal capture error:', e);
    }
  };

  // 6. Countdown Timer
  useEffect(() => {
    if (timeLeft <= 0) {
      handleFinalSubmit();
      return;
    }
    const timer = setInterval(() => {
      setTimeLeft((t) => t - 1);
    }, 1000);
    return () => clearInterval(timer);
  }, [timeLeft]);

  // 7. Periodic Autosave (every 10 seconds)
  useEffect(() => {
    const autosaveInterval = setInterval(() => {
      triggerAutosave();
    }, 10000);
    return () => clearInterval(autosaveInterval);
  }, [answers, sessionData.submission_id]);

  const triggerAutosave = async () => {
    try {
      const res = await authFetch('/api/submissions/autosave', {
        method: 'POST',
        body: JSON.stringify({
          submission_id: sessionData.submission_id,
          answers: answers
        })
      });
      if (res.ok) {
        setLastAutosave(new Date().toLocaleTimeString());
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleSelectOption = (option) => {
    const updated = { ...answers, [String(currentQ.id)]: option };
    setAnswers(updated);
  };

  const handleFinalSubmit = async () => {
    setIsSubmitting(true);
    try {
      const res = await authFetch('/api/submissions/submit', {
        method: 'POST',
        body: JSON.stringify({
          submission_id: sessionData.submission_id,
          answers: answers
        })
      });
      if (!res.ok) throw new Error('Submission failed');
      const result = await res.json();
      onFinishExam(result);
    } catch (err) {
      alert('Error submitting exam: ' + err.message);
      setIsSubmitting(false);
    }
  };

  const formatTimer = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
  };

  const answeredCount = Object.keys(answers).length;

  return (
    <div className="container" style={{ maxWidth: '1180px', padding: '1.25rem' }}>
      {/* Hidden Canvas for Frame Processing */}
      <canvas ref={canvasRef} style={{ display: 'none' }} />

      {/* Pre-Exam Personalized Calibration Modal */}
      {calibrationPhase && (
        <div className="fintech-modal-overlay">
          <div className="fintech-modal-content" style={{ maxWidth: '640px', padding: '2.5rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem', marginBottom: '1.5rem' }}>
              <div style={{
                width: '44px',
                height: '44px',
                borderRadius: '12px',
                background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#04130d',
                boxShadow: '0 0 16px rgba(16, 185, 129, 0.35)'
              }}>
                <ShieldCheck size={24} strokeWidth={2.5} />
              </div>
              <div>
                <h2 style={{ fontSize: '1.4rem', fontWeight: 800 }}>
                  Personalized Biometric Calibration
                </h2>
                <div style={{ fontSize: '0.78rem', color: 'var(--ft-text-muted)' }}>
                  Calibrating your personal posture baseline and acoustic profile to prevent false positives.
                </div>
              </div>
            </div>

            {/* Step 1: Video Posture Baseline */}
            <div style={{
              padding: '1.25rem',
              backgroundColor: 'rgba(255, 255, 255, 0.02)',
              borderRadius: '12px',
              marginBottom: '1.25rem',
              border: '1px solid var(--ft-border-subtle)'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.6rem' }}>
                <span style={{ fontSize: '0.88rem', fontWeight: 700, color: '#ffffff', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <Video size={16} color="var(--ft-primary-light)" />
                  1. Video Posture Baseline
                </span>
                <span style={{ fontSize: '0.8rem', color: calibrationProgress >= 100 ? 'var(--ft-primary-light)' : 'var(--ft-text-secondary)', fontWeight: 700 }}>
                  {calibrationProgress}% Complete
                </span>
              </div>
              <div style={{
                width: '100%',
                height: '8px',
                backgroundColor: 'rgba(255, 255, 255, 0.08)',
                borderRadius: '9999px',
                overflow: 'hidden',
                marginBottom: '0.5rem'
              }}>
                <div style={{
                  width: `${calibrationProgress}%`,
                  height: '100%',
                  background: 'linear-gradient(90deg, #10b981, #34d399)',
                  transition: 'width 0.3s ease'
                }} />
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--ft-text-muted)' }}>
                Please sit upright and look naturally at the display while the AI calculates your individual head yaw, pitch, and position baseline.
              </div>
            </div>

            {/* Step 2: Audio Voice Enrollment */}
            <div style={{
              padding: '1.25rem',
              backgroundColor: 'rgba(255, 255, 255, 0.02)',
              borderRadius: '12px',
              marginBottom: '1.75rem',
              border: '1px solid var(--ft-border-subtle)'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.6rem' }}>
                <span style={{ fontSize: '0.88rem', fontWeight: 700, color: '#ffffff', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <Mic size={16} color="var(--ft-accent-cyan)" />
                  2. Voice Biometrics Enrollment (Resemblyzer)
                </span>
                {audioEnrolled ? (
                  <span className="badge badge-success" style={{ fontSize: '0.72rem' }}>✓ Enrolled</span>
                ) : micDenied ? (
                  <span className="badge badge-warning" style={{ fontSize: '0.72rem' }}>Video-Only Mode</span>
                ) : (
                  <span style={{ fontSize: '0.72rem', color: '#fbbf24', fontWeight: 600 }}>Awaiting Voice Sample</span>
                )}
              </div>

              {!micDenied && (
                <>
                  <div style={{
                    fontSize: '0.85rem',
                    color: '#ffffff',
                    backgroundColor: 'rgba(0, 0, 0, 0.4)',
                    padding: '0.85rem 1rem',
                    borderRadius: '8px',
                    borderLeft: '3px solid var(--ft-primary)',
                    fontStyle: 'italic',
                    marginBottom: '1rem',
                    lineHeight: 1.45
                  }}>
                    "{verificationPhrase}"
                  </div>

                  <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', flexWrap: 'wrap' }}>
                    {!audioEnrolled && !isRecordingAudio && (
                      <button
                        onClick={startRecordingPhrase}
                        className="btn-secondary"
                        style={{ fontSize: '0.82rem', padding: '0.55rem 1.1rem' }}
                      >
                        <Mic size={14} color="var(--ft-primary-light)" />
                        <span>Start Reading Verification Phrase</span>
                      </button>
                    )}
                    {isRecordingAudio && (
                      <button
                        onClick={stopRecordingPhrase}
                        className="btn-danger"
                        style={{ fontSize: '0.82rem', padding: '0.55rem 1.1rem' }}
                      >
                        <span className="pulse-dot pulse-red" style={{ width: '6px', height: '6px' }} />
                        <span>Stop & Enroll Voice Profile</span>
                      </button>
                    )}
                    {!audioEnrolled && (
                      <button
                        onClick={() => setMicDenied(true)}
                        style={{
                          background: 'transparent',
                          border: 'none',
                          color: 'var(--ft-text-muted)',
                          fontSize: '0.78rem',
                          cursor: 'pointer',
                          textDecoration: 'underline'
                        }}
                      >
                        Skip (Video-Only Mode)
                      </button>
                    )}
                  </div>
                </>
              )}

              {micDenied && (
                <div style={{ fontSize: '0.75rem', color: 'var(--ft-text-muted)' }}>
                  Microphone is disabled. Proctoring will execute in personalized video-only baseline mode.
                </div>
              )}
            </div>

            {/* Launch Exam Button */}
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem' }}>
              <button
                disabled={calibrationProgress < 20}
                onClick={() => setCalibrationPhase(false)}
                className="btn-primary"
                style={{
                  fontSize: '0.92rem',
                  padding: '0.75rem 1.8rem',
                  opacity: calibrationProgress < 20 ? 0.45 : 1,
                  cursor: calibrationProgress < 20 ? 'not-allowed' : 'pointer'
                }}
              >
                {calibrationProgress >= 100
                  ? 'Begin Examination →'
                  : calibrationProgress >= 20
                  ? 'Proceed with Baseline →'
                  : 'Calibrating Biometrics...'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Top Session Bar (Fintech HUD Header) */}
      <div className="fintech-card" style={{
        padding: '1rem 1.5rem',
        marginBottom: '1.25rem',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: '1rem'
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 800 }}>{sessionData.exam_title}</h2>
            <span className="badge badge-success" style={{ fontSize: '0.7rem' }}>
              Baseline Active
            </span>
            {audioEnrolled && (
              <span className="badge badge-info" style={{ fontSize: '0.7rem' }}>
                Voice Armed
              </span>
            )}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--ft-text-muted)', marginTop: '0.2rem' }}>
            Session #{sessionData.submission_id} • AES-256 Authenticated Session • Mode: {micDenied ? 'Video-Only' : 'Full Fused'}
          </div>
        </div>

        {/* Timer & Autosave */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: '0.7rem', color: 'var(--ft-text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
              {lastAutosave ? `Autosaved ${lastAutosave}` : 'Autosave Active'}
            </div>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.35rem',
              fontFamily: 'var(--font-heading)',
              fontSize: '1.45rem',
              fontWeight: 800,
              color: timeLeft < 300 ? '#f43f5e' : (timeLeft < 600 ? '#f59e0b' : 'var(--ft-primary-light)')
            }}>
              <Clock size={18} />
              <span>{formatTimer(timeLeft)}</span>
            </div>
          </div>

          <button
            onClick={() => setShowSubmitModal(true)}
            className="btn-primary"
            style={{ fontSize: '0.88rem', padding: '0.65rem 1.3rem' }}
          >
            Submit Examination
          </button>
        </div>
      </div>

      {/* Main Layout (Left: Question Card, Right: Proctoring Feed & Palette) */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 310px', gap: '1.25rem' }}>
        {/* LEFT: Current Question Card */}
        <div className="fintech-card" style={{
          padding: '2rem',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          minHeight: '480px'
        }}>
          {currentQ ? (
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
                <span className="badge badge-success" style={{ fontSize: '0.78rem' }}>
                  Question {currentQIndex + 1} of {questions.length}
                </span>
                <span style={{ fontSize: '0.8rem', color: 'var(--ft-text-secondary)', fontWeight: 600 }}>
                  Weight: {currentQ.marks} Marks
                </span>
              </div>

              <h3 style={{ fontSize: '1.25rem', fontWeight: 600, lineHeight: 1.5, marginBottom: '1.75rem' }}>
                {currentQ.question_text}
              </h3>

              {/* Options */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                {currentQ.options.map((option, idx) => {
                  const isSelected = answers[String(currentQ.id)] === option;
                  return (
                    <div
                      key={idx}
                      onClick={() => handleSelectOption(option)}
                      style={{
                        padding: '0.95rem 1.25rem',
                        borderRadius: '12px',
                        backgroundColor: isSelected ? 'rgba(16, 185, 129, 0.12)' : 'rgba(255, 255, 255, 0.02)',
                        border: isSelected ? '1px solid var(--ft-primary-border)' : '1px solid var(--ft-border-subtle)',
                        boxShadow: isSelected ? '0 0 15px rgba(16, 185, 129, 0.15)' : 'none',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.85rem',
                        transition: 'all 0.2s ease'
                      }}
                    >
                      <div style={{
                        width: '20px',
                        height: '20px',
                        borderRadius: '50%',
                        border: isSelected ? '5px solid var(--ft-primary)' : '2px solid var(--ft-border-base)',
                        backgroundColor: isSelected ? '#ffffff' : 'transparent',
                        flexShrink: 0
                      }} />
                      <span style={{
                        fontSize: '0.92rem',
                        color: isSelected ? '#ffffff' : 'var(--ft-text-primary)',
                        fontWeight: isSelected ? 600 : 400
                      }}>
                        {option}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          ) : (
            <p style={{ color: 'var(--ft-text-muted)' }}>No questions loaded.</p>
          )}

          {/* Navigation Prev/Next */}
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginTop: '2rem',
            borderTop: '1px solid var(--ft-border-subtle)',
            paddingTop: '1.25rem'
          }}>
            <button
              onClick={() => setCurrentQIndex((prev) => Math.max(0, prev - 1))}
              disabled={currentQIndex === 0}
              className="btn-secondary"
              style={{ fontSize: '0.85rem', padding: '0.55rem 1.1rem' }}
            >
              <ChevronLeft size={16} /> Previous
            </button>

            <span style={{ fontSize: '0.82rem', color: 'var(--ft-text-muted)' }}>
              {answeredCount} of {questions.length} Answered
            </span>

            <button
              onClick={() => setCurrentQIndex((prev) => Math.min(questions.length - 1, prev + 1))}
              disabled={currentQIndex === questions.length - 1}
              className="btn-primary"
              style={{ fontSize: '0.85rem', padding: '0.55rem 1.1rem' }}
            >
              Next <ChevronRight size={16} />
            </button>
          </div>
        </div>

        {/* RIGHT: AI Proctoring Webcam & Question Palette */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {/* Webcam Box */}
          <div className="fintech-card" style={{ padding: '1rem', textAlign: 'center' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.65rem' }}>
              <span className="fintech-stat-label" style={{ fontSize: '0.7rem' }}>AI Proctor HUD</span>
              <span className={`badge ${proctorStatus.suspicious ? 'badge-error' : 'badge-success'}`} style={{ fontSize: '0.68rem' }}>
                <span className={`pulse-dot ${proctorStatus.suspicious ? 'pulse-red' : 'pulse-green'}`} style={{ width: '5px', height: '5px' }} />
                {proctorStatus.suspicious
                  ? `Flagged (${Math.round((proctorStatus.cheating_prob || 0.85) * 100)}% Risk)`
                  : 'Compliant'}
              </span>
            </div>

            <div style={{
              position: 'relative',
              width: '100%',
              height: '160px',
              backgroundColor: '#000000',
              borderRadius: '10px',
              overflow: 'hidden',
              border: `2px solid ${proctorStatus.suspicious ? '#f43f5e' : 'var(--ft-primary)'}`,
              boxShadow: proctorStatus.suspicious ? '0 0 15px rgba(244, 63, 94, 0.4)' : 'none'
            }}>
              <video
                ref={videoRef}
                autoPlay
                playsInline
                muted
                style={{ width: '100%', height: '100%', objectFit: 'cover' }}
              />
              {cameraError && (
                <div style={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  right: 0,
                  bottom: 0,
                  padding: '1rem',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  backgroundColor: 'rgba(0, 0, 0, 0.88)',
                  color: '#fda4af',
                  fontSize: '0.75rem'
                }}>
                  {cameraError}
                </div>
              )}
            </div>

            {proctorStatus.suspicious && (
              <div style={{
                marginTop: '0.65rem',
                fontSize: '0.72rem',
                color: '#fda4af',
                backgroundColor: 'rgba(244, 63, 94, 0.12)',
                border: '1px solid rgba(244, 63, 94, 0.3)',
                padding: '0.5rem 0.75rem',
                borderRadius: '8px',
                textAlign: 'left'
              }}>
                <div style={{ fontWeight: 700, marginBottom: '0.25rem', color: '#fda4af', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                  <ShieldAlert size={13} /> Modality Alerts:
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem' }}>
                  {proctorStatus.flags?.map((f, i) => {
                    let label = f;
                    if (f.includes('PHONE')) label = 'Smartphone Device Detected';
                    else if (f.includes('BOOK')) label = 'Prohibited Notes / Textbook';
                    else if (f.includes('EAR')) label = 'Hand Near Ear (Audio device)';
                    else if (f.includes('MOUTH')) label = 'Hand Covering Mouth';
                    else if (f.includes('PERSON')) label = 'Multiple Persons Detected';
                    else if (f.includes('NO_FACE')) label = 'No Candidate in Frame';
                    return (
                      <span key={i} style={{ color: '#fecdd3' }}>
                        • {label}
                      </span>
                    );
                  })}
                </div>
              </div>
            )}
          </div>

          {/* Question Palette Matrix */}
          <div className="fintech-card" style={{ padding: '1.25rem' }}>
            <span className="fintech-stat-label" style={{ display: 'block', marginBottom: '0.75rem' }}>
              Question Palette
            </span>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '0.45rem' }}>
              {questions.map((q, idx) => {
                const isAnswered = answers[String(q.id)] !== undefined;
                const isCurrent = currentQIndex === idx;
                return (
                  <button
                    key={q.id}
                    onClick={() => setCurrentQIndex(idx)}
                    style={{
                      aspectRatio: '1',
                      borderRadius: '8px',
                      border: isCurrent ? '2px solid #ffffff' : '1px solid var(--ft-border-subtle)',
                      backgroundColor: isAnswered ? 'var(--ft-primary)' : 'rgba(255, 255, 255, 0.03)',
                      color: isAnswered ? '#04130d' : '#ffffff',
                      fontWeight: 700,
                      fontSize: '0.82rem',
                      cursor: 'pointer',
                      transition: 'all 0.15s ease'
                    }}
                  >
                    {idx + 1}
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      </div>

      {/* Submit Confirmation Modal */}
      {showSubmitModal && (
        <div className="fintech-modal-overlay">
          <div className="fintech-modal-content" style={{ maxWidth: '440px', textAlign: 'center' }}>
            <div style={{
              width: '54px',
              height: '54px',
              borderRadius: '50%',
              backgroundColor: 'var(--ft-primary-muted)',
              border: '1px solid var(--ft-primary-border)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 1.25rem',
              color: 'var(--ft-primary-light)'
            }}>
              <CheckCircle size={28} />
            </div>

            <h3 style={{ fontSize: '1.35rem', fontWeight: 800, marginBottom: '0.4rem' }}>
              Submit Examination?
            </h3>
            <p style={{ color: 'var(--ft-text-secondary)', fontSize: '0.88rem', marginBottom: '1.75rem', lineHeight: 1.5 }}>
              You have answered <strong>{answeredCount} of {questions.length}</strong> questions.
              Once submitted, your answers will be locked, AES-256 encrypted, and auto-graded by the proctoring engine.
            </p>

            <div style={{ display: 'flex', gap: '0.75rem' }}>
              <button
                onClick={handleFinalSubmit}
                disabled={isSubmitting}
                className="btn-primary"
                style={{ flex: 1, padding: '0.75rem' }}
              >
                {isSubmitting ? 'Submitting...' : 'Confirm Submission'}
              </button>
              <button
                onClick={() => setShowSubmitModal(false)}
                disabled={isSubmitting}
                className="btn-secondary"
                style={{ flex: 1 }}
              >
                Return to Exam
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
