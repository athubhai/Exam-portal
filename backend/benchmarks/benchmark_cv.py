import os
import sys
import json
import csv
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix

# Add backend directory to sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from ai_engine.classifier import proctor_classifier, FEATURE_NAMES

RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

def run_stratified_5fold_cv():
    print("=" * 70)
    print("RUNNING STRATIFIED 5-FOLD CROSS-VALIDATION HARNESS")
    print("=" * 70)

    # 1. Generate standard dataset from ProctoringClassifier
    print("[1/3] Generating Mendeley distribution dataset (N=5,500, Features=37)...")
    X, y = proctor_classifier.generate_synthetic_mendeley_dataset(n_samples=5500, random_state=42)
    print(f"      Samples: {len(X)} | Features: {len(FEATURE_NAMES)} | Class 0: {np.sum(y == 0)} | Class 1: {np.sum(y == 1)}")

    # 2. Stratified 5-Fold Cross-Validation
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    fold_metrics = []
    
    print("\n[2/3] Evaluating 5 Stratified Folds on Behavioral Proctoring RF...")
    for fold, (train_idx, val_idx) in enumerate(skf.split(X, y), 1):
        X_train, X_val = X[train_idx], X[val_idx]
        y_train, y_val = y[train_idx], y[val_idx]

        clf = RandomForestClassifier(n_estimators=100, max_depth=12, random_state=42 + fold, n_jobs=-1)
        clf.fit(X_train, y_train)
        y_pred = clf.predict(X_val)

        acc = accuracy_score(y_val, y_pred)
        prec = precision_score(y_val, y_pred, zero_division=0)
        rec = recall_score(y_val, y_pred, zero_division=0)
        f1 = f1_score(y_val, y_pred, zero_division=0)
        
        cm = confusion_matrix(y_val, y_pred)
        tn, fp, fn, tp = cm.ravel()
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
        fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0

        metrics = {
            "fold": fold,
            "train_samples": len(train_idx),
            "val_samples": len(val_idx),
            "accuracy": float(acc),
            "precision": float(prec),
            "recall": float(rec),
            "f1_score": float(f1),
            "fpr": float(fpr),
            "fnr": float(fnr),
            "tn": int(tn),
            "fp": int(fp),
            "fn": int(fn),
            "tp": int(tp)
        }
        fold_metrics.append(metrics)
        print(f"      Fold {fold}: Acc={acc:.4f} | Prec={prec:.4f} | Rec={rec:.4f} | F1={f1:.4f} | FPR={fpr:.4f}")

    # Compute Aggregate Mean ± Std
    keys = ["accuracy", "precision", "recall", "f1_score", "fpr", "fnr"]
    summary = {}
    for k in keys:
        vals = [m[k] for m in fold_metrics]
        summary[f"{k}_mean"] = float(np.mean(vals))
        summary[f"{k}_std"] = float(np.std(vals))

    # 3. Repeat 5-Fold CV on Phone/Bezel RF Detector for complete verification
    print("\n[3/3] Evaluating 5 Stratified Folds on Hand-Occluded Phone/Bezel RF...")
    phone_skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    np.random.seed(42)
    X_phone, y_phone = [], []
    for _ in range(3000):
        # Background objects, clothes, desk clutter, occasional rectangular items (calculators/mousepads)
        is_rect_clutter = (np.random.rand() < 0.04)
        ar = np.random.uniform(1.3, 2.2) if is_rect_clutter else np.random.uniform(0.6, 4.5)
        sol = np.random.uniform(0.68, 0.85) if is_rect_clutter else np.random.uniform(0.25, 0.72)
        ext = np.random.uniform(0.55, 0.75) if is_rect_clutter else np.random.uniform(0.15, 0.60)
        area = np.random.uniform(0.003, 0.35)
        elev = np.random.uniform(0.30, 0.85) if is_rect_clutter else np.random.uniform(0.60, 0.99)
        unif = np.random.uniform(0.40, 0.75) if is_rect_clutter else np.random.uniform(0.10, 0.55)
        X_phone.append([ar, sol, ext, area, elev, unif])
        y_phone.append(0)
    for _ in range(2500):
        # Real phones held in hand, with 2-4 fingers occluding bezel corners
        is_heavy_occlusion = (np.random.rand() < 0.08)
        ar = np.random.normal(1.92, 0.32)
        sol = np.random.uniform(0.58, 0.80) if is_heavy_occlusion else np.random.uniform(0.68, 0.98)
        ext = np.random.uniform(0.48, 0.75) if is_heavy_occlusion else np.random.uniform(0.58, 0.96)
        area = np.random.uniform(0.006, 0.24)
        elev = np.random.uniform(0.15, 0.82)
        unif = np.random.uniform(0.42, 0.80) if is_heavy_occlusion else np.random.uniform(0.54, 0.98)
        X_phone.append([ar, sol, ext, area, elev, unif])
        y_phone.append(1)
    X_phone = np.array(X_phone)
    y_phone = np.array(y_phone)

    phone_fold_metrics = []
    for fold, (train_idx, val_idx) in enumerate(phone_skf.split(X_phone, y_phone), 1):
        X_train, X_val = X_phone[train_idx], X_phone[val_idx]
        y_train, y_val = y_phone[train_idx], y_phone[val_idx]
        p_clf = RandomForestClassifier(n_estimators=100, max_depth=12, random_state=42 + fold)
        p_clf.fit(X_train, y_train)
        y_pred = p_clf.predict(X_val)

        phone_fold_metrics.append({
            "fold": fold,
            "accuracy": float(accuracy_score(y_val, y_pred)),
            "precision": float(precision_score(y_val, y_pred, zero_division=0)),
            "recall": float(recall_score(y_val, y_pred, zero_division=0)),
            "f1_score": float(f1_score(y_val, y_pred, zero_division=0))
        })

    phone_summary = {}
    for k in ["accuracy", "precision", "recall", "f1_score"]:
        vals = [m[k] for m in phone_fold_metrics]
        phone_summary[f"{k}_mean"] = float(np.mean(vals))
        phone_summary[f"{k}_std"] = float(np.std(vals))

    # Save to JSON
    output_data = {
        "model_name": "ProctoringClassifier_RandomForest",
        "dataset_info": {
            "total_samples": len(X),
            "features_count": len(FEATURE_NAMES),
            "normal_samples": int(np.sum(y == 0)),
            "suspicious_samples": int(np.sum(y == 1)),
            "n_folds": 5
        },
        "fold_metrics": fold_metrics,
        "summary": summary,
        "phone_detector_summary": phone_summary
    }

    json_path = os.path.join(RESULTS_DIR, "cv_metrics.json")
    with open(json_path, "w") as f:
        json.dump(output_data, f, indent=2)
    print(f"\n[Saved JSON]: {json_path}")

    # Save to CSV
    csv_path = os.path.join(RESULTS_DIR, "cv_metrics.csv")
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Fold", "Train Size", "Val Size", "Accuracy", "Precision", "Recall", "F1 Score", "FPR", "FNR"])
        for m in fold_metrics:
            writer.writerow([
                m["fold"], m["train_samples"], m["val_samples"],
                f"{m['accuracy']:.4f}", f"{m['precision']:.4f}", f"{m['recall']:.4f}",
                f"{m['f1_score']:.4f}", f"{m['fpr']:.4f}", f"{m['fnr']:.4f}"
            ])
        writer.writerow([
            "MEAN", "-", "-",
            f"{summary['accuracy_mean']:.4f}", f"{summary['precision_mean']:.4f}", f"{summary['recall_mean']:.4f}",
            f"{summary['f1_score_mean']:.4f}", f"{summary['fpr_mean']:.4f}", f"{summary['fnr_mean']:.4f}"
        ])
        writer.writerow([
            "STD", "-", "-",
            f"{summary['accuracy_std']:.4f}", f"{summary['precision_std']:.4f}", f"{summary['recall_std']:.4f}",
            f"{summary['f1_score_std']:.4f}", f"{summary['fpr_std']:.4f}", f"{summary['fnr_std']:.4f}"
        ])
    print(f"[Saved CSV]:  {csv_path}")

    # Print markdown table
    print("\n" + "=" * 70)
    print("STRATIFIED 5-FOLD CROSS-VALIDATION SUMMARY TABLE (Mendeley 37-Feature RF)")
    print("=" * 70)
    print(f"{'Fold':<8} | {'Accuracy':<10} | {'Precision':<10} | {'Recall':<10} | {'F1-Score':<10} | {'FPR':<8}")
    print("-" * 65)
    for m in fold_metrics:
        print(f"Fold {m['fold']:<3} | {m['accuracy']:<10.4f} | {m['precision']:<10.4f} | {m['recall']:<10.4f} | {m['f1_score']:<10.4f} | {m['fpr']:<8.4f}")
    print("-" * 65)
    print(f"{'MEAN':<8} | {summary['accuracy_mean']:<10.4f} | {summary['precision_mean']:<10.4f} | {summary['recall_mean']:<10.4f} | {summary['f1_score_mean']:<10.4f} | {summary['fpr_mean']:<8.4f}")
    print(f"{'STD':<8} | {summary['accuracy_std']:<10.4f} | {summary['precision_std']:<10.4f} | {summary['recall_std']:<10.4f} | {summary['f1_score_std']:<10.4f} | {summary['fpr_std']:<8.4f}")
    print("=" * 70)

    print("\nPHONE BEZEL RANDOM FOREST 5-FOLD CV SUMMARY:")
    print(f"  Accuracy:  {phone_summary['accuracy_mean']:.4f} ± {phone_summary['accuracy_std']:.4f}")
    print(f"  Precision: {phone_summary['precision_mean']:.4f} ± {phone_summary['precision_std']:.4f}")
    print(f"  Recall:    {phone_summary['recall_mean']:.4f} ± {phone_summary['recall_std']:.4f}")
    print(f"  F1-Score:  {phone_summary['f1_score_mean']:.4f} ± {phone_summary['f1_score_std']:.4f}")
    print("=" * 70)

    return output_data

if __name__ == "__main__":
    run_stratified_5fold_cv()
