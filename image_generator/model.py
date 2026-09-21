from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

import numpy as np
from PIL import Image, ImageDraw


class ImageRecognitionModel:
    """A lightweight image recognition demo based on color and texture features."""

    def __init__(self, labels: Iterable[str] | None = None):
        self.labels = list(labels or ["nature", "city", "portrait", "object"])
        self._centroids: dict[str, np.ndarray] = {}

    def _load_image(self, image_source):
        if isinstance(image_source, (str, Path)):
            return Image.open(image_source).convert("RGB")
        if isinstance(image_source, Image.Image):
            return image_source.convert("RGB")
        raise TypeError("Unsupported image source type")

    def _extract_features(self, image: Image.Image) -> np.ndarray:
        rgb = np.asarray(image, dtype=np.float32) / 255.0
        r, g, b = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]

        mean = np.array([r.mean(), g.mean(), b.mean()])
        std = np.array([r.std(), g.std(), b.std()])

        gray = np.dot(rgb[..., :3], [0.299, 0.587, 0.114])
        brightness = gray.mean()
        contrast = gray.std()

        hsv = np.array(Image.fromarray(np.uint8(rgb * 255)).convert("HSV"), dtype=np.float32) / 255.0
        saturation = hsv[:, :, 1].mean()

        features = np.concatenate([
            mean,
            std,
            np.array([brightness, contrast, saturation], dtype=np.float32),
        ])
        return features

    def fit(self, dataset):
        """Training data format: [(label, image_or_path), ...]."""
        centroids = {label: [] for label in self.labels}

        for label, image_source in dataset:
            if label not in centroids:
                centroids[label] = []
            features = self._extract_features(self._load_image(image_source))
            centroids[label].append(features)

        self._centroids = {
            label: np.mean(np.vstack(values), axis=0)
            for label, values in centroids.items()
            if values
        }
        return self

    def predict(self, image_source):
        if not self._centroids:
            raise ValueError("Model has not been trained yet. Call fit() before predict().")

        features = self._extract_features(self._load_image(image_source))
        scores = {
            label: float(np.linalg.norm(features - centroid))
            for label, centroid in self._centroids.items()
        }
        return min(scores, key=scores.get)

    def predict_image_path(self, image_path):
        return self.predict(image_path)

    def save(self, path):
        output = {"labels": self.labels, "centroids": {k: v.tolist() for k, v in self._centroids.items()}}
        Path(path).write_text(json.dumps(output), encoding="utf-8")

    @classmethod
    def load(cls, path):
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        model = cls(labels=payload.get("labels", []))
        model._centroids = {k: np.array(v, dtype=np.float32) for k, v in payload.get("centroids", {}).items()}
        return model


def build_demo_dataset():
    """Creates a small synthetic dataset for demo purposes."""
    samples = []

    for label, color in {
        "nature": (74, 138, 84),
        "city": (107, 118, 145),
        "portrait": (180, 120, 92),
        "object": (150, 60, 60),
    }.items():
        image = Image.new("RGB", (64, 64), color)
        draw = ImageDraw.Draw(image)

        if label == "nature":
            for i in range(12):
                draw.ellipse((i * 5, 28 + (i % 3) * 8, i * 5 + 12, 48 + (i % 3) * 8), fill=(30, 120, 40))
        elif label == "city":
            for x in range(8):
                draw.rectangle((x * 7, 12, x * 7 + 4, 58), fill=(220, 220, 220))
                draw.rectangle((x * 7 + 2, 18, x * 7 + 6, 52), fill=(160, 160, 170))
        elif label == "portrait":
            draw.ellipse((18, 10, 46, 38), fill=(240, 210, 190))
            draw.ellipse((20, 8, 44, 30), fill=(90, 60, 45))
            draw.rectangle((24, 38, 40, 55), fill=(100, 80, 80))
        else:
            for i in range(8):
                draw.rectangle((10 + i * 6, 16 + (i % 3) * 5, 22 + i * 6, 52), fill=(220, 170, 110))

        samples.append((label, image))

    return samples


if __name__ == "__main__":
    model = ImageRecognitionModel(labels=["nature", "city", "portrait", "object"])
    dataset = build_demo_dataset()
    model.fit(dataset)

    test_image = Image.new("RGB", (64, 64), (80, 140, 90))
    draw = ImageDraw.Draw(test_image)
    for i in range(8):
        draw.ellipse((i * 7, 20 + (i % 2) * 10, i * 7 + 12, 40 + (i % 2) * 10), fill=(25, 100, 40))

    print(f"Predicted class: {model.predict(test_image)}")
