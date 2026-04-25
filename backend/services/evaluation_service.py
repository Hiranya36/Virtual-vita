import os
import time
import warnings
from datetime import datetime
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, confusion_matrix, precision_recall_fscore_support
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split

# Suppress noisy sklearn warning for high class-count / sample ratio datasets.
warnings.filterwarnings(
    "ignore",
    message="The number of unique classes is greater than 50% of the number of samples.*",
    category=UserWarning,
)


class ModelEvaluator:
    """Evaluates the disease prediction model on dataset.csv."""

    def __init__(self, dataset_path: str = None):
        if dataset_path is None:
            dataset_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "dataset")
            cleaned = os.path.join(dataset_dir, "dataset_cleaned.csv")
            dataset_path = cleaned if os.path.exists(cleaned) else os.path.join(dataset_dir, "dataset.csv")
        self.dataset_path = dataset_path

    def _load_dataset(self) -> pd.DataFrame:
        return pd.read_csv(self.dataset_path)

    def _build_feature_space(self, df: pd.DataFrame) -> List[str]:
        all_symptoms = set()
        for col in df.columns[1:]:
            for val in df[col].dropna().unique():
                all_symptoms.add(str(val).strip().replace("_", " ").lower())
        return sorted(list(all_symptoms))

    def _vectorize(self, df: pd.DataFrame, all_symptoms: List[str]) -> Tuple[np.ndarray, np.ndarray]:
        symptom_to_idx = {sym: i for i, sym in enumerate(all_symptoms)}
        rows = []
        labels = []

        for _, row in df.iterrows():
            vector = np.zeros(len(all_symptoms), dtype=int)
            for col in df.columns[1:]:
                val = row[col]
                if pd.notna(val):
                    clean = str(val).strip().replace("_", " ").lower()
                    idx = symptom_to_idx.get(clean)
                    if idx is not None:
                        vector[idx] = 1
            rows.append(vector)
            labels.append(str(row["Disease"]).strip())

        return np.array(rows), np.array(labels)

    def _measure_response_times(self, model, x_test: np.ndarray, sample_size: int = 120) -> Dict:
        if len(x_test) == 0:
            return {"average_ms": 0, "p95_ms": 0, "max_ms": 0}

        n = min(sample_size, len(x_test))
        indices = np.linspace(0, len(x_test) - 1, n, dtype=int)
        elapsed_ms: List[float] = []
        for i in indices:
            start = time.perf_counter()
            _ = model.predict([x_test[i]])
            elapsed_ms.append((time.perf_counter() - start) * 1000)

        return {
            "average_ms": round(float(np.mean(elapsed_ms)), 3),
            "p95_ms": round(float(np.percentile(elapsed_ms, 95)), 3),
            "max_ms": round(float(np.max(elapsed_ms)), 3),
        }

    def generate_report(self) -> Dict:
        df = self._load_dataset()
        all_symptoms = self._build_feature_space(df)
        x, y = self._vectorize(df, all_symptoms)

        unique_classes = np.unique(y)
        stratify = y if len(unique_classes) > 1 else None
        x_train, x_test, y_train, y_test = train_test_split(
            x,
            y,
            test_size=0.35,
            random_state=42,
            stratify=stratify,
        )

        model = RandomForestClassifier(n_estimators=180, random_state=42)

        train_start = time.perf_counter()
        model.fit(x_train, y_train)
        train_time_ms = round((time.perf_counter() - train_start) * 1000, 2)

        y_pred = model.predict(x_test)
        accuracy = accuracy_score(y_test, y_pred)

        p_macro, r_macro, f1_macro, _ = precision_recall_fscore_support(
            y_test,
            y_pred,
            average="macro",
            zero_division=0,
        )
        p_weighted, r_weighted, f1_weighted, _ = precision_recall_fscore_support(
            y_test,
            y_pred,
            average="weighted",
            zero_division=0,
        )

        response_metrics = self._measure_response_times(model, x_test)
        labels = sorted(np.unique(y_test))
        cm = confusion_matrix(y_test, y_pred, labels=labels)

        # Per-class metrics for transparent error analysis.
        p_cls, r_cls, f1_cls, support_cls = precision_recall_fscore_support(
            y_test,
            y_pred,
            labels=labels,
            average=None,
            zero_division=0,
        )
        per_class_metrics = []
        for idx, label in enumerate(labels):
            per_class_metrics.append(
                {
                    "class": label,
                    "precision": round(float(p_cls[idx]), 4),
                    "recall": round(float(r_cls[idx]), 4),
                    "f1_score": round(float(f1_cls[idx]), 4),
                    "support": int(support_cls[idx]),
                }
            )

        # K-fold cross-validation for more realistic generalization estimate.
        # Cap folds based on the smallest class count.
        class_counts = pd.Series(y).value_counts()
        min_class_count = int(class_counts.min()) if not class_counts.empty else 2
        folds = max(2, min(5, min_class_count))
        skf = StratifiedKFold(n_splits=folds, shuffle=True, random_state=42)
        cv_scores = cross_val_score(model, x, y, cv=skf, scoring="accuracy")

        report = {
            "generated_at": datetime.now().isoformat(),
            "dataset_summary": {
                "rows": int(df.shape[0]),
                "feature_symptom_count": int(len(all_symptoms)),
                "disease_classes": int(len(unique_classes)),
                "train_rows": int(len(x_train)),
                "test_rows": int(len(x_test)),
            },
            "model_summary": {
                "algorithm": "RandomForestClassifier",
                "n_estimators": 180,
                "training_time_ms": train_time_ms,
            },
            "metrics": {
                "accuracy": round(float(accuracy), 4),
                "macro_precision": round(float(p_macro), 4),
                "macro_recall": round(float(r_macro), 4),
                "macro_f1": round(float(f1_macro), 4),
                "weighted_precision": round(float(p_weighted), 4),
                "weighted_recall": round(float(r_weighted), 4),
                "weighted_f1": round(float(f1_weighted), 4),
            },
            "cross_validation": {
                "folds": int(folds),
                "accuracy_scores": [round(float(v), 4) for v in cv_scores.tolist()],
                "mean_accuracy": round(float(np.mean(cv_scores)), 4),
                "std_accuracy": round(float(np.std(cv_scores)), 4),
            },
            "per_class_metrics": per_class_metrics,
            "confusion_matrix": {
                "labels": labels,
                "matrix": cm.tolist(),
            },
            "response_time": response_metrics,
        }
        return report
