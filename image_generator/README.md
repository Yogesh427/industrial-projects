# Image Generator

This package adds a lightweight image recognition model for the PhoenixML project.

## What it does

It uses simple image features such as average color, contrast, and saturation to classify a small set of visual categories:

- nature
- city
- portrait
- object

## Quick usage

```python
from PIL import Image
from image_generator import ImageRecognitionModel

model = ImageRecognitionModel(labels=["nature", "city", "portrait", "object"])
dataset = [
    ("nature", Image.new("RGB", (64, 64), (74, 138, 84))),
    ("city", Image.new("RGB", (64, 64), (107, 118, 145))),
    ("portrait", Image.new("RGB", (64, 64), (180, 120, 92))),
    ("object", Image.new("RGB", (64, 64), (150, 60, 60))),
]
model.fit(dataset)
print(model.predict(Image.new("RGB", (64, 64), (80, 140, 90))))
```

This is a lightweight demo model intended for educational and prototype use.
