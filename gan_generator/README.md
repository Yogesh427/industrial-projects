# GAN Generator

This package creates simple synthetic images using a lightweight GAN-like generator.

## What it does

It does not train a large neural network, but it creates simple visual patterns in a GAN-inspired style for demos and education.

## Usage

```python
from gan_generator import SimpleGANGenerator

model = SimpleGANGenerator(seed=7)
image = model.generate("nature")
image.save("nature_demo.png")
```

Also supported:
- nature
- city
- portrait
- object

## Output

The generated image is saved as a PNG file or returned as a PIL image object.
