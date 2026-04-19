from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


def build_model(random_state: int = 42) -> Pipeline:
    return Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            (
                "classifier",
                RandomForestClassifier(
                    n_estimators=300,
                    max_depth=None,
                    min_samples_split=2,
                    random_state=random_state,
                    n_jobs=-1,
                ),
            ),
        ]
    )


def train_model(
    features: np.ndarray,
    labels: np.ndarray,
    class_names: list[str],
    test_size: float = 0.2,
    random_state: int = 42,
) -> tuple[Pipeline, dict[str, object]]:
    model = build_model(random_state=random_state)

    if len(np.unique(labels)) < 2:
        raise ValueError("Training requires at least two genres.")

    x_train, x_test, y_train, y_test = train_test_split(
        features,
        labels,
        test_size=test_size,
        stratify=labels,
        random_state=random_state,
    )

    model.fit(x_train, y_train)
    predictions = model.predict(x_test)
    metrics = {
        "accuracy": float(accuracy_score(y_test, predictions)),
        "report": classification_report(
            y_test,
            predictions,
            target_names=class_names,
            zero_division=0,
        ),
        "train_samples": int(len(x_train)),
        "test_samples": int(len(x_test)),
    }
    return model, metrics


def save_model(model: Pipeline, class_names: list[str], sample_rate: int, clip_duration: int, output_path: str | Path) -> None:
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    bundle = {
        "model": model,
        "class_names": class_names,
        "sample_rate": sample_rate,
        "clip_duration": clip_duration,
    }
    joblib.dump(bundle, destination)


def load_model(model_path: str | Path) -> dict[str, object]:
    return joblib.load(model_path)
