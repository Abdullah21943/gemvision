"""Train the gemstone-type CNN classifier (transfer learning on EfficientNetB0).

Corresponds to proposal Phase 3 / Objective 4: >=80% accuracy across the 87
classes in the Kaggle "gemstones-images" dataset.

Expects the dataset already downloaded via ml/download_datasets.py, with the
layout Kaggle ships it in:
    ml/data/gemstones-images/train/<class_name>/*.jpg
    ml/data/gemstones-images/test/<class_name>/*.jpg
If your download has a different top-level folder name, adjust DATA_DIR below.

Usage:
    python ml/train_cnn.py [--epochs 20] [--batch-size 32] [--freeze-base]

Output:
    backend/models/gemstone_cnn.keras
    backend/models/class_indices.json
    ml/reports/cnn_training_history.png
    ml/reports/cnn_classification_report.txt
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ML_DIR = Path(__file__).resolve().parent
DATA_DIR = ML_DIR / "data" / "gemstones-images"
BACKEND_MODELS_DIR = ML_DIR.parent / "backend" / "models"
REPORTS_DIR = ML_DIR / "reports"

IMAGE_SIZE = 224


def build_model(num_classes: int, freeze_base: bool):
    import tensorflow as tf
    from tensorflow.keras import layers, models
    from tensorflow.keras.applications import EfficientNetB0

    base_model = EfficientNetB0(
        include_top=False,
        weights="imagenet",
        input_shape=(IMAGE_SIZE, IMAGE_SIZE, 3),
        pooling="avg",
    )
    base_model.trainable = not freeze_base

    inputs = tf.keras.Input(shape=(IMAGE_SIZE, IMAGE_SIZE, 3))
    x = layers.RandomFlip("horizontal")(inputs)
    x = layers.RandomRotation(0.15)(x)
    x = layers.RandomZoom(0.15)(x)
    x = layers.RandomBrightness(0.15)(x)
    x = base_model(x, training=not freeze_base)
    x = layers.Dropout(0.3)(x)
    outputs = layers.Dense(num_classes, activation="softmax")(x)

    model = models.Model(inputs, outputs)
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-4),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )
    return model


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument(
        "--freeze-base",
        action="store_true",
        help="Freeze the EfficientNetB0 backbone (faster, use for a quick CPU run).",
    )
    args = parser.parse_args()

    train_dir = DATA_DIR / "train"
    test_dir = DATA_DIR / "test"
    if not train_dir.exists():
        raise SystemExit(
            f"Dataset not found at {train_dir}. Run `python ml/download_datasets.py` "
            "first, or check the folder layout matches what this script expects."
        )

    import tensorflow as tf
    from sklearn.metrics import classification_report

    train_ds = tf.keras.utils.image_dataset_from_directory(
        train_dir,
        image_size=(IMAGE_SIZE, IMAGE_SIZE),
        batch_size=args.batch_size,
        label_mode="categorical",
    )
    class_names = train_ds.class_names
    num_classes = len(class_names)
    print(f"Found {num_classes} classes")

    val_ds = None
    if test_dir.exists():
        val_ds = tf.keras.utils.image_dataset_from_directory(
            test_dir,
            image_size=(IMAGE_SIZE, IMAGE_SIZE),
            batch_size=args.batch_size,
            label_mode="categorical",
        )

    normalization = tf.keras.layers.Rescaling(1.0 / 255)
    train_ds = train_ds.map(lambda x, y: (normalization(x), y)).prefetch(tf.data.AUTOTUNE)
    if val_ds is not None:
        val_ds_eval = val_ds
        val_ds = val_ds.map(lambda x, y: (normalization(x), y)).prefetch(tf.data.AUTOTUNE)

    model = build_model(num_classes, freeze_base=args.freeze_base)
    model.summary()

    callbacks = [
        tf.keras.callbacks.EarlyStopping(monitor="val_loss" if val_ds else "loss", patience=4, restore_best_weights=True),
        tf.keras.callbacks.ReduceLROnPlateau(monitor="val_loss" if val_ds else "loss", factor=0.5, patience=2),
    ]

    history = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=args.epochs,
        callbacks=callbacks,
    )

    BACKEND_MODELS_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    model_path = BACKEND_MODELS_DIR / "gemstone_cnn.keras"
    model.save(model_path)
    print(f"Saved model -> {model_path}")

    class_indices = {name: idx for idx, name in enumerate(class_names)}
    class_indices_path = BACKEND_MODELS_DIR / "class_indices.json"
    with open(class_indices_path, "w", encoding="utf-8") as f:
        json.dump(class_indices, f, indent=2)
    print(f"Saved class indices -> {class_indices_path}")

    try:
        import matplotlib.pyplot as plt

        fig, axes = plt.subplots(1, 2, figsize=(10, 4))
        axes[0].plot(history.history["accuracy"], label="train")
        if "val_accuracy" in history.history:
            axes[0].plot(history.history["val_accuracy"], label="val")
        axes[0].set_title("Accuracy")
        axes[0].legend()

        axes[1].plot(history.history["loss"], label="train")
        if "val_loss" in history.history:
            axes[1].plot(history.history["val_loss"], label="val")
        axes[1].set_title("Loss")
        axes[1].legend()

        fig.tight_layout()
        fig.savefig(REPORTS_DIR / "cnn_training_history.png")
        print(f"Saved training curves -> {REPORTS_DIR / 'cnn_training_history.png'}")
    except Exception as exc:  # noqa: BLE001
        print(f"Could not save training plot: {exc}")

    if val_ds is not None:
        import numpy as np

        y_true, y_pred = [], []
        for batch_x, batch_y in val_ds_eval:
            preds = model.predict(normalization(batch_x), verbose=0)
            y_true.extend(np.argmax(batch_y.numpy(), axis=1))
            y_pred.extend(np.argmax(preds, axis=1))

        report = classification_report(y_true, y_pred, target_names=class_names, zero_division=0)
        report_path = REPORTS_DIR / "cnn_classification_report.txt"
        report_path.write_text(report, encoding="utf-8")
        print(report)
        print(f"Saved classification report -> {report_path}")


if __name__ == "__main__":
    main()
