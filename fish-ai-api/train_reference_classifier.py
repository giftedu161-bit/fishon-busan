"""Train the small FishOn beta image classifier from user-labelled reference photos.

This is intentionally a supplementary classifier. The main EfficientDet model remains
the object detector; this model helps identify a cropped/single-fish photograph.
"""

import json
import random
from collections import Counter
from pathlib import Path

import numpy as np
import torch
from PIL import Image, ImageEnhance, ImageOps
from torch import nn
from torch.utils.data import DataLoader, Dataset, WeightedRandomSampler

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "fish-ai-model" / "training-reference-manifest.json"
TEMP = Path.home() / "AppData" / "Local" / "Temp"
OUTPUT = Path(__file__).resolve().parent / "models" / "reference_classifier.pt"
IMAGE_SIZE = 128
EPOCHS = 90


class FishDataset(Dataset):
    def __init__(self, samples, labels, augment=False):
        self.samples, self.labels, self.augment = samples, labels, augment

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, index):
        label, path = self.samples[index]
        image = Image.open(path).convert("RGB")
        if self.augment:
            if random.random() < .5:
                image = ImageOps.mirror(image)
            image = image.rotate(random.uniform(-10, 10), fillcolor=(255, 255, 255))
            image = ImageEnhance.Brightness(image).enhance(random.uniform(.85, 1.15))
        image = ImageOps.fit(image, (IMAGE_SIZE, IMAGE_SIZE), method=Image.Resampling.BILINEAR)
        array = np.asarray(image, dtype=np.float32).transpose(2, 0, 1) / 255.0
        tensor = (torch.from_numpy(array) - torch.tensor([.485, .456, .406])[:, None, None]) / torch.tensor([.229, .224, .225])[:, None, None]
        return tensor, self.labels.index(label)


class ReferenceFishNet(nn.Module):
    def __init__(self, classes):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3, 24, 3, padding=1), nn.BatchNorm2d(24), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(24, 48, 3, padding=1), nn.BatchNorm2d(48), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(48, 96, 3, padding=1), nn.BatchNorm2d(96), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(96, 128, 3, padding=1), nn.ReLU(), nn.AdaptiveAvgPool2d(1),
        )
        self.head = nn.Sequential(nn.Flatten(), nn.Dropout(.25), nn.Linear(128, classes))

    def forward(self, image):
        return self.head(self.features(image))


def source_path(value):
    path = Path(value)
    return path if path.is_absolute() else TEMP / path


def main():
    random.seed(7); np.random.seed(7); torch.manual_seed(7)
    torch.set_num_threads(min(6, max(1, torch.get_num_threads())))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    samples = [(label, source_path(file_name)) for label, file_name in manifest["samples"]]
    missing = [str(path) for _, path in samples if not path.exists()]
    if missing:
        raise SystemExit("Missing reference photos:\n" + "\n".join(missing))
    labels = list(manifest["species"].keys())
    counts = Counter(label for label, _ in samples)
    weights = [1 / counts[label] for label, _ in samples]
    loader = DataLoader(FishDataset(samples, labels, augment=True), batch_size=8,
                        sampler=WeightedRandomSampler(weights, num_samples=len(samples), replacement=True))
    model = ReferenceFishNet(len(labels))
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.0015, weight_decay=0.0001)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, EPOCHS)
    loss_fn = nn.CrossEntropyLoss(label_smoothing=.04)
    model.train()
    for epoch in range(EPOCHS):
        total_loss = 0.0
        for images, targets in loader:
            optimizer.zero_grad()
            loss = loss_fn(model(images), targets)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        scheduler.step()
        if (epoch + 1) % 15 == 0:
            print(f"epoch {epoch + 1}/{EPOCHS} loss={total_loss / len(loader):.4f}")
    model.eval()
    correct = 0
    with torch.no_grad():
        for image, target in DataLoader(FishDataset(samples, labels), batch_size=8):
            correct += int((model(image).argmax(1) == target).sum())
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    torch.save({"state_dict": model.state_dict(), "labels": labels, "imageSize": IMAGE_SIZE,
                "sampleCount": len(samples), "accuracyOnReferences": correct / len(samples)}, OUTPUT)
    print(f"saved={OUTPUT} accuracy_on_references={correct / len(samples):.3f}")


if __name__ == "__main__":
    main()
