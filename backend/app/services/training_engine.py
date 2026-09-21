from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import uuid

import numpy as np
import pickle

from app.services.compute import runtime_info


ARTIFACT_DIR = Path(__file__).resolve().parents[2] / "artifacts"


def _label_column(rows: list[dict[str, str]]) -> str:
    columns = rows[0].keys()
    return next((column for column in columns if column.lower() in {"label", "class", "target"}), "")


def _split(values, labels):
    from sklearn.model_selection import train_test_split

    counts = np.unique(labels, return_counts=True)[1]
    if len(counts) < 2:
        raise ValueError("Training requires at least two different labels.")
    if min(counts) < 2 or len(labels) < 6:
        return values, values, labels, labels
    return train_test_split(values, labels, test_size=0.2, random_state=42, stratify=labels)


def _numeric_features(rows: list[dict[str, str]], target_column: str) -> tuple[np.ndarray, list[str]]:
    from sklearn.impute import SimpleImputer

    columns = [key for key in rows[0] if key != target_column and key.lower() not in {"filename", "mode", "text"}]
    if not columns:
        raise ValueError("Add numeric feature columns before training.")
    try:
        values = np.array([[float(row.get(column, 0) or 0) for column in columns] for row in rows], dtype=float)
    except ValueError as error:
        raise ValueError("This model requires numeric feature columns.") from error
    return SimpleImputer(strategy="median").fit_transform(values), columns


def _train_linear_regression(rows: list[dict[str, str]]) -> dict:
    from sklearn.linear_model import LinearRegression
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
    from sklearn.model_selection import train_test_split

    target_column = _label_column(rows)
    if not target_column:
        raise ValueError("Linear Regression needs a target column named target, label, or class.")
    try:
        targets = np.array([float(row[target_column]) for row in rows], dtype=float)
    except ValueError as error:
        raise ValueError("Linear Regression target values must be numeric, for example 12.5.") from error
    values, feature_columns = _numeric_features(rows, target_column)
    if len(rows) >= 6:
        train_values, validation_values, train_targets, validation_targets = train_test_split(values, targets, test_size=0.2, random_state=42)
    else:
        train_values, validation_values, train_targets, validation_targets = values, values, targets, targets
    model = LinearRegression().fit(train_values, train_targets)
    predictions = model.predict(validation_values)
    artifact_id = f"{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    artifact_path = ARTIFACT_DIR / f"{artifact_id}.pkl"
    with artifact_path.open("wb") as artifact_file:
        pickle.dump(model, artifact_file)
    return {
        "artifact_id": artifact_id,
        "artifact_path": str(artifact_path),
        "algorithm": "linear-regression",
        "rows_used": len(rows),
        "features": feature_columns,
        "labels": [],
        "metrics": {
            "r2": round(float(r2_score(validation_targets, predictions)), 3),
            "mae": round(float(mean_absolute_error(validation_targets, predictions)), 3),
            "rmse": round(float(mean_squared_error(validation_targets, predictions) ** 0.5), 3),
        },
        "metric_type": "regression",
        "compute": runtime_info(),
    }


def _train_vision(rows: list[dict[str, str]], algorithm: str) -> dict:
    import torch
    from torch import nn
    from sklearn.metrics import accuracy_score, f1_score

    label_column = _label_column(rows)
    feature_columns = [key for key in rows[0] if key != label_column and key.lower() not in {"filename", "mode", "text"}]
    if not feature_columns:
        raise ValueError("Image training needs numeric image features.")
    labels = sorted({row[label_column] for row in rows})
    if len(labels) < 2:
        raise ValueError("Training requires at least two different labels.")
    label_ids = {label: index for index, label in enumerate(labels)}
    values = np.array([[float(row.get(column, 0) or 0) for column in feature_columns] for row in rows], dtype=np.float32)
    targets = np.array([label_ids[row[label_column]] for row in rows], dtype=np.int64)
    train_values, validation_values, train_labels, validation_labels = _split(values, targets)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = nn.Sequential(nn.Linear(values.shape[1], 32), nn.ReLU(), nn.Linear(32, len(labels))).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
    loss_function = nn.CrossEntropyLoss()
    x_train = torch.tensor(train_values, device=device)
    y_train = torch.tensor(train_labels, device=device)
    model.train()
    for _ in range(25):
        optimizer.zero_grad()
        loss = loss_function(model(x_train), y_train)
        loss.backward()
        optimizer.step()
    model.eval()
    with torch.no_grad():
        predictions = model(torch.tensor(validation_values, device=device)).argmax(dim=1).cpu().numpy()
    artifact_id = f"{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    artifact_path = ARTIFACT_DIR / f"{artifact_id}.pt"
    torch.save({"state_dict": model.state_dict(), "features": feature_columns, "labels": labels}, artifact_path)
    return {
        "artifact_id": artifact_id,
        "artifact_path": str(artifact_path),
        "algorithm": algorithm,
        "rows_used": len(rows),
        "features": feature_columns,
        "labels": labels,
        "metrics": {
            "accuracy": round(float(accuracy_score(validation_labels, predictions)), 3),
            "validation_score": round(float(f1_score(validation_labels, predictions, average="weighted", zero_division=0)), 3),
        },
        "compute": {"backend": "cuda" if device.type == "cuda" else "cpu", "cuda_available": device.type == "cuda", "device": str(device)},
    }


def train(rows: list[dict[str, str]], algorithm: str) -> dict:
    if algorithm == "linear-regression":
        return _train_linear_regression(rows)
    if algorithm in {"image-recognition", "vision-classifier"}:
        return _train_vision(rows, algorithm)

    from sklearn.ensemble import RandomForestClassifier
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import accuracy_score, f1_score
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler

    label_column = _label_column(rows)
    if not label_column:
        raise ValueError("Add a label, class, or target column before training.")
    labels = np.array([row[label_column] for row in rows])
    feature_columns = [
        key for key in rows[0]
        if key != label_column and key.lower() not in {"filename", "mode", "text"}
    ]
    text_column = next((key for key in rows[0] if key.lower() == "text"), None)

    if algorithm == "spam-classifier" and text_column:
        values = np.array([row.get(text_column, "") for row in rows])
        model = Pipeline([
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1)),
            ("classifier", LogisticRegression(max_iter=500)),
        ])
        feature_names = [text_column]
    else:
        try:
            values = np.array([[float(row.get(column, 0) or 0) for column in feature_columns] for row in rows])
        except ValueError as error:
            raise ValueError("This algorithm needs numeric feature columns, or use Spam Classifier for text.") from error
        if not feature_columns:
            raise ValueError("No numeric feature columns were found in the dataset.")
        classifier = RandomForestClassifier(n_estimators=120, random_state=42, n_jobs=-1) if algorithm in {"random-forest", "image-recognition", "vision-classifier"} else LogisticRegression(max_iter=500)
        model = Pipeline([("scale", StandardScaler()), ("classifier", classifier)])
        feature_names = feature_columns

    train_values, validation_values, train_labels, validation_labels = _split(values, labels)
    model.fit(train_values, train_labels)
    predictions = model.predict(validation_values)
    artifact_id = f"{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    artifact_path = ARTIFACT_DIR / f"{artifact_id}.joblib"
    with artifact_path.open("wb") as artifact_file:
        pickle.dump(model, artifact_file)

    return {
        "artifact_id": artifact_id,
        "artifact_path": str(artifact_path),
        "algorithm": algorithm,
        "rows_used": len(rows),
        "features": feature_names,
        "labels": sorted(set(labels.tolist())),
        "metrics": {
            "accuracy": round(float(accuracy_score(validation_labels, predictions)), 3),
            "validation_score": round(float(f1_score(validation_labels, predictions, average="weighted", zero_division=0)), 3),
        },
        "metric_type": "classification",
        "compute": runtime_info(),
    }