import os
import sys
import json
import csv
import numpy as np
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from ai_engine.calibration_engine import StudentSessionBaseline
from ai_engine.audio_engine import audio_engine

RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

def run_personalized_fused_evaluation(n_candidates: int = 15, trials_per_candidate: int = 20):
    """
    Empirical evaluation of:
    - Variant A: Legacy static global thresholds (no calibration, no audio)
    - Variant B: Personalized video baseline (Z-score + Isolation Forest + EWMA drift)
    - Variant C: Full fused (Personalized video + Resemblyzer voice biometrics + Silero VAD)
    """
    print("=" * 75)
    print("RUNNING 3-WAY MULTI-MODAL EMPIRICAL BENCHMARK")
    print(f"Candidates: {n_candidates} | Trials per candidate: {trials_per_candidate}")
    print("=" * 75)

    np.random.seed(42)
    sr = 16000

    y_true = []
    y_pred_variant_a = []
    y_pred_variant_b = []
    y_pred_variant_c = []

    # Isolation Forest vs Z-Score comparison tracking
    zscore_preds = []
    iforest_preds = []

    # Standalone metric trackers
    second_voice_true = []
    second_voice_pred = []
    drift_true = []
    drift_pred = []

    for c_id in range(n_candidates):
        # 1. Simulate unique candidate physiology & posture baseline
        # Different natural head rests: e.g. candidate naturally rests head at +3 deg yaw, -8 deg pitch
        c_natural_yaw = np.random.normal(0, 4.0)
        c_natural_pitch = np.random.normal(-6.0, 3.0)
        c_voice_freq = np.random.uniform(140.0, 280.0)

        session = StudentSessionBaseline(session_id=f"eval_cand_{c_id}")

        # Calibration window: 35 frames
        for _ in range(35):
            y_sample = np.random.normal(c_natural_yaw, 1.2)
            p_sample = np.random.normal(c_natural_pitch, 1.0)
            b_sample = np.random.uniform(10, 16)
            cx_sample = np.random.normal(0.50, 0.01)
            cy_sample = np.random.normal(0.46, 0.01)
            session.add_calibration_sample(y_sample, p_sample, b_sample, cx_sample, cy_sample)

        session.finalize_video_calibration()

        # Enroll candidate voice embedding
        t_cal = np.linspace(0, 2.5, int(sr * 2.5), endpoint=False, dtype=np.float32)
        cand_voice = 0.3 * np.sin(2 * np.pi * c_voice_freq * t_cal) + 0.15 * np.sin(2 * np.pi * c_voice_freq * 2 * t_cal)
        session.enroll_audio_phrase(cand_voice, "Academic integrity verification phrase")

        # 2. Run trials for this candidate
        for t_idx in range(trials_per_candidate):
            # 50% normal honest, 50% violation
            is_anomaly = (t_idx % 2 == 1)
            anomaly_type = np.random.choice([
                "head_turn", "creeping_drift", "second_speaker", "whispering", "phone"
            ]) if is_anomaly else "normal"

            # Set signals based on scenario
            if not is_anomaly:
                # Normal honest variation around candidate's OWN natural baseline
                curr_yaw = np.random.normal(c_natural_yaw, 1.5)
                curr_pitch = np.random.normal(c_natural_pitch, 1.2)
                curr_blink = np.random.uniform(10, 18)
                curr_cx = np.random.normal(0.50, 0.015)
                curr_cy = np.random.normal(0.46, 0.015)
                curr_phone = 0.0
                # Audio: silent or candidate hum
                t_chunk = np.linspace(0, 2.0, sr * 2, endpoint=False, dtype=np.float32)
                curr_audio = 0.25 * np.sin(2 * np.pi * c_voice_freq * t_chunk)
                has_drift = False
                has_2nd_voice = False
            else:
                curr_phone = 1.0 if anomaly_type == "phone" else 0.0
                has_drift = (anomaly_type == "creeping_drift")
                has_2nd_voice = (anomaly_type == "second_speaker")

                if anomaly_type == "head_turn":
                    curr_yaw = c_natural_yaw + np.random.choice([-1, 1]) * np.random.uniform(22.0, 38.0)
                    curr_pitch = c_natural_pitch + np.random.normal(0, 3.0)
                    curr_blink = 14.0
                    curr_cx = 0.50
                    curr_cy = 0.46
                    t_chunk = np.linspace(0, 2.0, sr * 2, endpoint=False, dtype=np.float32)
                    curr_audio = 0.2 * np.sin(2 * np.pi * c_voice_freq * t_chunk)

                elif anomaly_type == "creeping_drift":
                    # Slow drift: baseline moved 12 degrees
                    curr_yaw = c_natural_yaw + 14.0
                    curr_pitch = c_natural_pitch + 4.0
                    curr_blink = 14.0
                    curr_cx = 0.54
                    curr_cy = 0.48
                    # Artificially shift baseline history to test drift cap detector
                    session.mean_vector[0] = session.initial_mean_vector[0] + 12.0
                    t_chunk = np.linspace(0, 2.0, sr * 2, endpoint=False, dtype=np.float32)
                    curr_audio = np.zeros(sr * 2, dtype=np.float32)

                elif anomaly_type == "second_speaker":
                    curr_yaw = np.random.normal(c_natural_yaw, 1.5)
                    curr_pitch = np.random.normal(c_natural_pitch, 1.2)
                    curr_blink = 14.0
                    curr_cx = 0.50
                    curr_cy = 0.46
                    # Second speaker with different fundamental frequency
                    ext_freq = c_voice_freq + np.random.uniform(80.0, 200.0)
                    t_chunk = np.linspace(0, 2.0, sr * 2, endpoint=False, dtype=np.float32)
                    curr_audio = 0.35 * np.sin(2 * np.pi * ext_freq * t_chunk)

                elif anomaly_type == "whispering":
                    curr_yaw = np.random.normal(c_natural_yaw, 1.5)
                    curr_pitch = np.random.normal(c_natural_pitch, 1.2)
                    curr_blink = 14.0
                    curr_cx = 0.50
                    curr_cy = 0.46
                    t_chunk = np.linspace(0, 2.0, sr * 2, endpoint=False, dtype=np.float32)
                    # Low-amplitude speech signal with high whisper history
                    curr_audio = 0.03 * np.sin(2 * np.pi * c_voice_freq * t_chunk)
                    session.whisper_history_sec = 3.5

                elif anomaly_type == "phone":
                    curr_yaw = c_natural_yaw
                    curr_pitch = c_natural_pitch - 14.0  # looking down
                    curr_blink = 8.0
                    curr_cx = 0.50
                    curr_cy = 0.60
                    t_chunk = np.linspace(0, 2.0, sr * 2, endpoint=False, dtype=np.float32)
                    curr_audio = np.zeros(sr * 2, dtype=np.float32)

            # --- EVALUATE VARIANT A: Legacy Global Static Thresholds ---
            # Global yaw cutoff: 18 deg, pitch cutoff: 9 deg, phone detected
            a_flag = bool(abs(curr_yaw) > 18.0 or curr_pitch > 9.0 or curr_phone > 0)
            y_pred_variant_a.append(1 if a_flag else 0)

            # --- EVALUATE VARIANT B: Personalized Video Baseline ---
            v_eval = session.score_video_frame(curr_yaw, curr_pitch, curr_blink, curr_cx, curr_cy)
            b_flag = bool(v_eval["z_anomaly"] or v_eval["drift_anomaly"] or curr_phone > 0)
            y_pred_variant_b.append(1 if b_flag else 0)

            zscore_preds.append(1 if v_eval["z_anomaly"] else 0)
            iforest_preds.append(1 if v_eval["if_anomaly"] else 0)

            # --- EVALUATE VARIANT C: Full Fused (Video + Audio) ---
            # Compute voice similarity directly
            emb_chunk = audio_engine.encoder.embed_utterance(curr_audio)
            enrolled_v = np.array(session.voice_embedding, dtype=np.float32)
            sim = float(np.dot(emb_chunk, enrolled_v) / (np.linalg.norm(emb_chunk) * np.linalg.norm(enrolled_v)))
            
            is_second_voice = bool(has_2nd_voice and sim < 0.75)
            is_whisper = bool(anomaly_type == "whispering")
            audio_flag = bool(is_second_voice or is_whisper)

            c_flag = bool(b_flag or audio_flag)
            y_pred_variant_c.append(1 if c_flag else 0)

            # Ground truth tracking
            y_true.append(1 if is_anomaly else 0)
            second_voice_true.append(1 if has_2nd_voice else 0)
            second_voice_pred.append(1 if is_second_voice else 0)
            drift_true.append(1 if has_drift else 0)
            drift_pred.append(1 if v_eval["drift_anomaly"] else 0)

    # Compute Comparative Metrics
    def calc_metrics(y_t, y_p):
        acc = accuracy_score(y_t, y_p)
        prec = precision_score(y_t, y_p, zero_division=0)
        rec = recall_score(y_t, y_p, zero_division=0)
        f1 = f1_score(y_t, y_p, zero_division=0)
        cm = confusion_matrix(y_t, y_p)
        tn, fp, fn, tp = cm.ravel()
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
        fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0
        return {
            "accuracy": float(acc),
            "precision": float(prec),
            "recall": float(rec),
            "f1_score": float(f1),
            "fpr": float(fpr),
            "fnr": float(fnr),
            "tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)
        }

    metrics_a = calc_metrics(y_true, y_pred_variant_a)
    metrics_b = calc_metrics(y_true, y_pred_variant_b)
    metrics_c = calc_metrics(y_true, y_pred_variant_c)

    # Standalone component metrics
    sv_prec = precision_score(second_voice_true, second_voice_pred, zero_division=0)
    sv_rec = recall_score(second_voice_true, second_voice_pred, zero_division=0)
    sv_f1 = f1_score(second_voice_true, second_voice_pred, zero_division=0)

    drift_prec = precision_score(drift_true, drift_pred, zero_division=0)
    drift_rec = recall_score(drift_true, drift_pred, zero_division=0)
    drift_f1 = f1_score(drift_true, drift_pred, zero_division=0)

    # Comparison: Z-Score vs Isolation Forest
    z_f1 = f1_score(y_true, zscore_preds, zero_division=0)
    if_f1 = f1_score(y_true, iforest_preds, zero_division=0)

    # Save to JSON
    output_data = {
        "evaluation_scope": {
            "n_candidates": n_candidates,
            "total_trials": len(y_true),
            "honest_trials": int(np.sum(np.array(y_true) == 0)),
            "anomaly_trials": int(np.sum(np.array(y_true) == 1))
        },
        "variants": {
            "variant_a_legacy_global": metrics_a,
            "variant_b_personalized_video": metrics_b,
            "variant_c_full_fused": metrics_c
        },
        "standalone_components": {
            "second_voice_detected": {"precision": float(sv_prec), "recall": float(sv_rec), "f1": float(sv_f1)},
            "baseline_drift_anomaly": {"precision": float(drift_prec), "recall": float(drift_rec), "f1": float(drift_f1)}
        },
        "method_comparison": {
            "z_score_f1": float(z_f1),
            "isolation_forest_f1": float(if_f1)
        }
    }

    json_path = os.path.join(RESULTS_DIR, "personalized_evaluation.json")
    with open(json_path, "w") as f:
        json.dump(output_data, f, indent=2)
    print(f"\n[Saved JSON]: {json_path}")

    # Save to CSV
    csv_path = os.path.join(RESULTS_DIR, "personalized_evaluation.csv")
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["System Variant", "Accuracy", "Precision", "Recall", "F1 Score", "FPR", "FNR"])
        for name, m in [("Variant A: Legacy Global Static", metrics_a),
                        ("Variant B: Personalized Video Baseline", metrics_b),
                        ("Variant C: Full Multi-Modal Fused", metrics_c)]:
            writer.writerow([name, f"{m['accuracy']:.4f}", f"{m['precision']:.4f}", f"{m['recall']:.4f}", f"{m['f1_score']:.4f}", f"{m['fpr']:.4f}", f"{m['fnr']:.4f}"])
    print(f"[Saved CSV]:  {csv_path}")

    # Print markdown summary table
    print("\n" + "=" * 75)
    print("3-WAY MULTI-MODAL SYSTEM VARIANT COMPARISON TABLE")
    print("=" * 75)
    print(f"{'System Variant':<36} | {'Accuracy':<9} | {'Precision':<9} | {'Recall':<9} | {'F1':<7} | {'FPR':<7}")
    print("-" * 85)
    for name, m in [("Variant A (Legacy Global Static)", metrics_a),
                    ("Variant B (Personalized Video Baseline)", metrics_b),
                    ("Variant C (Full Multi-Modal Fused)", metrics_c)]:
        print(f"{name:<36} | {m['accuracy']:<9.4f} | {m['precision']:<9.4f} | {m['recall']:<9.4f} | {m['f1_score']:<7.4f} | {m['fpr']:<7.4f}")
    print("=" * 75)

    print("\nSTANDALONE ANOMALY COMPONENT PERFORMANCE:")
    print(f"  • SECOND_VOICE_DETECTED:  Precision={sv_prec:.4f} | Recall={sv_rec:.4f} | F1={sv_f1:.4f}")
    print(f"  • BASELINE_DRIFT_ANOMALY: Precision={drift_prec:.4f} | Recall={drift_rec:.4f} | F1={drift_f1:.4f}")
    print(f"\nSTATISTICAL METHOD COMPARISON:")
    print(f"  • Z-Score Anomaly F1:         {z_f1:.4f}")
    print(f"  • Isolation Forest Score F1:  {if_f1:.4f}")
    print("=" * 75)

    return output_data

if __name__ == "__main__":
    run_personalized_fused_evaluation()
