from __future__ import annotations

import math
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


class SimpleGANGenerator:
    """A tiny GAN-like image generator for educational use.

    It creates synthetic images by learning a few simple visual patterns
    and generating new samples from random latent vectors.
    """

    def __init__(self, image_size: int = 32, latent_dim: int = 3, seed: int | None = None):
        self.image_size = image_size
        self.latent_dim = latent_dim
        self.rng = random.Random(seed)
        self.patterns = {
            "nature": np.array([0.6, 0.8, 0.5], dtype=np.float32),
            "city": np.array([0.5, 0.5, 0.7], dtype=np.float32),
            "portrait": np.array([0.8, 0.6, 0.5], dtype=np.float32),
            "object": np.array([0.7, 0.4, 0.4], dtype=np.float32),
        }
        self.trained = False

    def _random_noise(self):
        return np.array([
            self.rng.uniform(-1.0, 1.0) for _ in range(self.latent_dim)
        ], dtype=np.float32)

    def _pattern_vector(self, style: str):
        if style not in self.patterns:
            raise ValueError(f"Unsupported style: {style}")
        return self.patterns[style].copy()

    def train(self, styles: list[str], epochs: int = 20):
        """A lightweight pseudo-training step to learn pattern controls."""
        for _ in range(epochs):
            for style in styles:
                vector = self._pattern_vector(style)
                noise = self._random_noise()
                self.patterns[style] = np.clip(0.9 * vector + 0.1 * noise, 0.0, 1.0)

        self.trained = True
        return self

    def generate(self, style: str, output_path: str | None = None, count: int = 1):
        if not self.trained:
            self.train(list(self.patterns.keys()))

        generated = []
        for _ in range(count):
            latent = self._random_noise()
            base = self._pattern_vector(style)
            mixed = np.clip(0.7 * base + 0.3 * latent, 0.0, 1.0)

            image = Image.new("RGB", (self.image_size, self.image_size), (0, 0, 0))
            draw = ImageDraw.Draw(image)

            for x in range(self.image_size):
                for y in range(self.image_size):
                    r = min(255, int((mixed[0] * x + mixed[1] * y) % 256))
                    g = min(255, int((mixed[1] * x + mixed[2] * y) % 256))
                    b = min(255, int((mixed[2] * x + mixed[0] * y) % 256))
                    draw.point((x, y), fill=(r, g, b))

            if style == "nature":
                draw.ellipse((5, 8, 26, 26), fill=(40, 150, 70))
                draw.rectangle((0, 22, self.image_size, self.image_size), fill=(90, 140, 80))
            elif style == "city":
                for i in range(5):
                    x0 = 4 + i * 6
                    draw.rectangle((x0, 10, x0 + 4, 26), fill=(200, 200, 210))
                draw.rectangle((0, 26, self.image_size, self.image_size), fill=(100, 110, 140))
            elif style == "portrait":
                draw.ellipse((10, 8, 22, 20), fill=(220, 180, 160))
                draw.rectangle((12, 22, 20, 30), fill=(120, 80, 70))
                draw.ellipse((8, 10, 24, 30), fill=(150, 120, 100))
            elif style == "object":
                draw.rectangle((10, 10, 22, 24), fill=(200, 120, 80))
                draw.line((10, 10, 18, 2), fill=(60, 60, 60), width=2)
                draw.line((22, 10, 30, 2), fill=(60, 60, 60), width=2)

            if output_path:
                target = Path(output_path)
                target.mkdir(parents=True, exist_ok=True)
                image.save(target / f"{style}_{len(generated) + 1}.png")

            generated.append(image)

        if count == 1:
            return generated[0]
        return generated


if __name__ == "__main__":
    generator = SimpleGANGenerator(seed=7)
    image = generator.generate("nature")
    image.save("generated_nature.png")
    print("Generated image saved as generated_nature.png")
