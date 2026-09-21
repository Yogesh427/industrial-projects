from __future__ import annotations

import argparse
from pathlib import Path
import random

import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset
from PIL import Image
from torchvision import transforms

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


class LabeledImages(Dataset):
    def __init__(self, root: Path, size: int):
        self.items = []
        self.labels = sorted(path.name for path in root.iterdir() if path.is_dir())
        self.label_ids = {label: index for index, label in enumerate(self.labels)}
        self.transform = transforms.Compose([
            transforms.Resize((size, size)),
            transforms.RandomHorizontalFlip(),
            transforms.ToTensor(),
            transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5)),
        ])
        for label in self.labels:
            for image in (root / label).iterdir():
                if image.suffix.lower() in IMAGE_EXTENSIONS:
                    self.items.append((image, self.label_ids[label]))
        if not self.items or len(self.labels) < 2:
            raise ValueError("Use at least two label folders with image files inside them.")

    def __len__(self):
        return len(self.items)

    def __getitem__(self, index):
        path, label = self.items[index]
        with Image.open(path) as image:
            return self.transform(image.convert("RGB")), label


class Generator(nn.Module):
    def __init__(self, noise_size: int, label_count: int):
        super().__init__()
        self.label = nn.Embedding(label_count, 16)
        self.network = nn.Sequential(
            nn.Linear(noise_size + 16, 256 * 8 * 8), nn.ReLU(True),
            nn.Unflatten(1, (256, 8, 8)),
            nn.ConvTranspose2d(256, 128, 4, 2, 1), nn.BatchNorm2d(128), nn.ReLU(True),
            nn.ConvTranspose2d(128, 64, 4, 2, 1), nn.BatchNorm2d(64), nn.ReLU(True),
            nn.ConvTranspose2d(64, 3, 4, 2, 1), nn.Tanh(),
        )

    def forward(self, noise, labels):
        return self.network(torch.cat((noise, self.label(labels)), dim=1))

    def forward_fusion(self, noise, label_groups):
        embeddings = self.label(label_groups).mean(dim=1)
        return self.network(torch.cat((noise, embeddings), dim=1))


class Discriminator(nn.Module):
    def __init__(self, label_count: int):
        super().__init__()
        self.label = nn.Embedding(label_count, 64 * 64)
        self.network = nn.Sequential(
            nn.Conv2d(4, 64, 4, 2, 1), nn.LeakyReLU(.2, True),
            nn.Conv2d(64, 128, 4, 2, 1), nn.BatchNorm2d(128), nn.LeakyReLU(.2, True),
            nn.Conv2d(128, 256, 4, 2, 1), nn.BatchNorm2d(256), nn.LeakyReLU(.2, True),
            nn.Flatten(), nn.Linear(256 * 8 * 8, 1), nn.Sigmoid(),
        )

    def forward(self, images, labels):
        label_map = self.label(labels).view(-1, 1, 64, 64)
        return self.network(torch.cat((images, label_map), dim=1))


def save_samples(generator, label_ids, names, output: Path, device, count: int, noise_size: int, fusion: str | None):
    output.mkdir(parents=True, exist_ok=True)
    generator.eval()
    with torch.no_grad():
        for index in range(count):
            if fusion:
                selected_names = [name.strip() for name in fusion.split("+") if name.strip()]
                missing = [name for name in selected_names if name not in label_ids]
                if missing:
                    raise ValueError(f"Fusion labels not found: {', '.join(missing)}")
                selected = torch.tensor([[label_ids[name] for name in selected_names]], device=device)
                filename_label = "_".join(selected_names)
                image = generator.forward_fusion(torch.randn(1, noise_size, device=device), selected)[0]
            else:
                selected = torch.tensor([random.randrange(len(names))], device=device)
                filename_label = names[selected.item()]
                image = generator(torch.randn(1, noise_size, device=device), selected)[0]
            image = ((image.clamp(-1, 1) + 1) * 127.5).byte().permute(1, 2, 0).cpu().numpy()
            Image.fromarray(image).save(output / f"fusion_{index + 1:04d}_{filename_label}.jpg", quality=92)


def train(args):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    dataset = LabeledImages(Path(args.data), args.size)
    loader = DataLoader(dataset, batch_size=args.batch, shuffle=True, num_workers=0)
    noise_size = 64
    generator = Generator(noise_size, len(dataset.labels)).to(device)
    discriminator = Discriminator(len(dataset.labels)).to(device)
    loss = nn.BCELoss()
    g_optimizer = torch.optim.Adam(generator.parameters(), lr=0.0002, betas=(0.5, 0.999))
    d_optimizer = torch.optim.Adam(discriminator.parameters(), lr=0.0002, betas=(0.5, 0.999))

    for epoch in range(args.epochs):
        for real, labels in loader:
            real, labels = real.to(device), labels.to(device)
            size = real.size(0)
            valid = torch.ones(size, 1, device=device)
            fake = torch.zeros(size, 1, device=device)
            noise = torch.randn(size, noise_size, device=device)
            generated = generator(noise, labels)
            d_optimizer.zero_grad()
            d_loss = (loss(discriminator(real, labels), valid) + loss(discriminator(generated.detach(), labels), fake)) / 2
            d_loss.backward()
            d_optimizer.step()
            g_optimizer.zero_grad()
            g_loss = loss(discriminator(generated, labels), valid)
            g_loss.backward()
            g_optimizer.step()
        print(f"epoch {epoch + 1}/{args.epochs} device={device} d_loss={d_loss.item():.4f} g_loss={g_loss.item():.4f}")

    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    torch.save({"generator": generator.state_dict(), "labels": dataset.labels}, output / "conditional_gan.pt")
    label_ids = {name: index for index, name in enumerate(dataset.labels)}
    save_samples(generator, label_ids, dataset.labels, output / "generated", device, args.samples, noise_size, args.fusion)
    print(f"Saved model: {output / 'conditional_gan.pt'}")
    print(f"Saved JPG samples: {output / 'generated'}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train a local conditional GAN on labeled image folders.")
    parser.add_argument("--data", required=True, help="Folder containing label subfolders")
    parser.add_argument("--output", default="gan_output")
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--batch", type=int, default=8)
    parser.add_argument("--size", type=int, default=64)
    parser.add_argument("--samples", type=int, default=20)
    parser.add_argument("--fusion", default=None, help="Combine labels, for example dogs+cats+birds")
    train(parser.parse_args())