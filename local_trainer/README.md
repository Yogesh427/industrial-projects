# Local Train / Remix / Improve

The original desktop tool creates JPG augmentations locally. The new `conditional_gan.py` is the real local GAN path and does not use PhoenixML or a browser.

## Dataset layout

```text
gan_data/
	dogs/
	cats/
	whales/
	wolves/
	birds/
```

## Train the GAN

```powershell
python -m pip install -r local_trainer\requirements.txt
python local_trainer\conditional_gan.py --data gan_data --output gan_output --epochs 20 --batch 8 --samples 50
```

The model is saved to:

```text
gan_output\conditional_gan.pt
```

Generated JPG images are saved to:

```text
gan_output\generated
```

Use 64x64 images and batch size 8 first with a 4 GB GPU. This is a real conditional GAN, but high-quality fusion creatures need more data and training than a small GPU can comfortably provide.
