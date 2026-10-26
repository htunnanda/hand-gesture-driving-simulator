
import argparse
import copy
import json
import random
from pathlib import Path

import torch
from torch import nn
from torch.utils.data import DataLoader, Subset
from torchvision import datasets, transforms

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    confusion_matrix,
)

CLASSES = ["fist", "left_dir", "palm", "right_dir"]
IMAGE_SIZE = 128
SEED = 42


# 1. CNN Model
class GestureCNN(nn.Module):
    def __init__(self, num_classes=4):
        super().__init__()

        self.features = nn.Sequential(
            nn.Conv2d(3, 32, 3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),

            nn.Conv2d(32, 64, 3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),

            nn.Conv2d(64, 128, 3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),

            nn.AdaptiveAvgPool2d((4, 4)),
        )

        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(128 * 4 * 4, 128),
            nn.ReLU(),
            nn.Dropout(0.35),
            nn.Linear(128, num_classes),
        )

    def forward(self, x):
        x = self.features(x)
        return self.classifier(x)


# 2. Stratified split: 70 / 15 / 15
def split_by_class(targets):
    rng = random.Random(SEED)
    train, val, test = [], [], []

    for label in sorted(set(targets)):
        ids = [
            i for i, y in enumerate(targets)
            if y == label
        ]
        rng.shuffle(ids)

        n = len(ids)
        n_train = int(n * 0.70)
        n_val = int(n * 0.15)

        if min(n_train, n_val, n - n_train - n_val) < 1:
            raise ValueError(f"Not enough data for class {label}")

        train.extend(ids[:n_train])
        val.extend(ids[n_train:n_train + n_val])
        test.extend(ids[n_train + n_val:])

    return train, val, test


# 3. Train / Validation
def run_epoch(model, loader, loss_fn, device, optimizer=None):
    training = optimizer is not None
    model.train(training)

    total_loss = 0
    correct = 0
    total = 0

    with torch.set_grad_enabled(training):
        for images, labels in loader:
            images = images.to(device)
            labels = labels.to(device)

            if training:
                optimizer.zero_grad(set_to_none=True)

            outputs = model(images)
            loss = loss_fn(outputs, labels)

            if training:
                loss.backward()
                optimizer.step()

            total_loss += loss.item() * labels.size(0)
            correct += (outputs.argmax(1) == labels).sum().item()
            total += labels.size(0)

    return total_loss / total, correct / total


# 4. Final F1 Evaluation
def evaluate(model, loader, device, class_names):
    model.eval()

    y_true = []
    y_pred = []

    with torch.no_grad():
        for images, labels in loader:
            outputs = model(images.to(device))
            predictions = outputs.argmax(dim=1)

            y_true.extend(labels.tolist())
            y_pred.extend(predictions.cpu().tolist())

    class_ids = list(range(len(class_names)))

    metrics = {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision_macro": float(precision_score(
            y_true, y_pred, labels=class_ids,
            average="macro", zero_division=0
        )),
        "recall_macro": float(recall_score(
            y_true, y_pred, labels=class_ids,
            average="macro", zero_division=0
        )),
        "f1_macro": float(f1_score(
            y_true, y_pred, labels=class_ids,
            average="macro", zero_division=0
        )),
    }

    print("\n===== TEST RESULTS =====")
    for key, value in metrics.items():
        print(f"{key}: {value:.4f}")

    print("\nClassification Report:")
    print(classification_report(
        y_true, y_pred,
        labels=class_ids,
        target_names=class_names,
        zero_division=0,
    ))

    print("\nConfusion Matrix:")
    print(confusion_matrix(
        y_true, y_pred, labels=class_ids
    ))

    return metrics


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--epochs", type=int, default=25)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument(
        "--out-dir", type=Path,
        default=Path("computer-vision/cnn-training/output")
    )
    args = parser.parse_args()

    torch.manual_seed(SEED)
    random.seed(SEED)

    device = torch.device(
        "cuda" if torch.cuda.is_available() else "cpu"
    )
    print("Device:", device)

    # No horizontal flip: it would swap left/right meaning
    train_transform = transforms.Compose([
        transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
        transforms.RandomRotation(8),
        transforms.ColorJitter(
            brightness=0.15,
            contrast=0.15
        ),
        transforms.ToTensor(),
    ])

    test_transform = transforms.Compose([
        transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
        transforms.ToTensor(),
    ])

    base = datasets.ImageFolder(str(args.data_dir))

    if set(base.classes) != set(CLASSES):
        raise ValueError(
            f"Expected {CLASSES}, found {base.classes}"
        )

    train_ids, val_ids, test_ids = split_by_class(base.targets)

    train_dataset = Subset(
        datasets.ImageFolder(
            str(args.data_dir), transform=train_transform
        ),
        train_ids
    )

    eval_dataset = datasets.ImageFolder(
        str(args.data_dir), transform=test_transform
    )

    val_dataset = Subset(eval_dataset, val_ids)
    test_dataset = Subset(eval_dataset, test_ids)

    train_loader = DataLoader(
        train_dataset, batch_size=args.batch_size,
        shuffle=True, num_workers=0
    )
    val_loader = DataLoader(
        val_dataset, batch_size=args.batch_size,
        shuffle=False, num_workers=0
    )
    test_loader = DataLoader(
        test_dataset, batch_size=args.batch_size,
        shuffle=False, num_workers=0
    )

    print("Classes:", base.class_to_idx)
    print(
        f"Train={len(train_ids)}, "
        f"Validation={len(val_ids)}, "
        f"Test={len(test_ids)}"
    )

    model = GestureCNN(
        num_classes=len(base.classes)
    ).to(device)

    optimizer = torch.optim.Adam(
        model.parameters(), lr=0.001
    )
    loss_fn = nn.CrossEntropyLoss()

    best_val_acc = -1
    best_state = None

    # 5. Training Loop
    for epoch in range(1, args.epochs + 1):
        train_loss, train_acc = run_epoch(
            model, train_loader, loss_fn, device, optimizer
        )

        val_loss, val_acc = run_epoch(
            model, val_loader, loss_fn, device
        )

        print(
            f"Epoch {epoch:02d}/{args.epochs} | "
            f"Train Loss={train_loss:.4f} "
            f"Acc={train_acc:.2%} | "
            f"Val Loss={val_loss:.4f} "
            f"Acc={val_acc:.2%}"
        )

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            best_state = copy.deepcopy(model.state_dict())

    # 6. Evaluate best model on test data
    model.load_state_dict(best_state)

    class_names = [
        name for name, index in sorted(
            base.class_to_idx.items(),
            key=lambda item: item[1]
        )
    ]

    print(f"\nBest Validation Accuracy: {best_val_acc:.2%}")

    metrics = evaluate(
        model, test_loader, device, class_names
    )

    # 7. Save model and results
    args.out_dir.mkdir(parents=True, exist_ok=True)

    model_path = args.out_dir / "gesture_cnn.pth"

    torch.save({
        "model_state_dict": model.cpu().state_dict(),
        "class_to_idx": base.class_to_idx,
        "image_size": [IMAGE_SIZE, IMAGE_SIZE],
    }, model_path)

    (args.out_dir / "labels.json").write_text(
        json.dumps(base.class_to_idx, indent=2),
        encoding="utf-8"
    )

    (args.out_dir / "metrics.json").write_text(
        json.dumps(metrics, indent=2),
        encoding="utf-8"
    )

    print("\nModel saved:", model_path.resolve())


if __name__ == "__main__":
    main()
