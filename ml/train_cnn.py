"""Train the gemstone-type CNN classifier (transfer learning on EfficientNetB0).

Corresponds to proposal Phase 3 / Objective 4: >=80% accuracy across the 87
classes in the Kaggle "gemstones-images" dataset.

Expects the dataset already downloaded via ml/download_datasets.py, with the
layout Kaggle ships it in:
    ml/data/gemstones-images/train/<class_name>/*.jpg
    ml/data/gemstones-images/test/<class_name>/*.jpg
If your download has a different top-level folder name, adjust DATA_DIR below.

Two-phase transfer learning: Phase 1 trains only the classification head with
the EfficientNetB0 backbone frozen (fast); Phase 2 unfreezes the backbone and
fine-tunes the whole network at a low learning rate (slow, but needed to
reach the 80% target -- the frozen head alone tops out around 55-65%).

Usage:
    python ml/train_cnn.py [--epochs 20] [--fine-tune-epochs 15] [--batch-size 32]
    python ml/train_cnn.py --freeze-base   # skip fine-tuning; quick CPU smoke test only

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


def build_model(num_classes: int):
    import tensorflow as tf
    from tensorflow.keras import layers, models
    from tensorflow.keras.applications import EfficientNetB0

    base_model = EfficientNetB0(
        include_top=False,
        weights="imagenet",
        input_shape=(IMAGE_SIZE, IMAGE_SIZE, 3),
        pooling="avg",
    )
    base_model.trainable = False

    inputs = tf.keras.Input(shape=(IMAGE_SIZE, IMAGE_SIZE, 3))
    x = layers.RandomFlip("horizontal")(inputs)
    x = layers.RandomRotation(0.15)(x)
    x = layers.RandomZoom(0.15)(x)
    x = layers.RandomBrightness(0.15)(x)
    # training=False here is intentional and permanent (it's baked into the
    # graph, independent of base_model.trainable at fit time): it keeps
    # BatchNorm layers in inference mode through both the frozen head-only
    # phase AND the later fine-tuning phase, which is the standard Keras
    # recipe for fine-tuning without destroying pretrained BN statistics.
    x = base_model(x, training=False)
    x = layers.Dropout(0.3)(x)
    outputs = layers.Dense(num_classes, activation="softmax")(x)

    model = models.Model(inputs, outputs)
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-4),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )
    return model, base_model


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=20, help="Frozen-head training phase.")
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument(
        "--freeze-base",
        action="store_true",
        help="Skip fine-tuning entirely: frozen-backbone head-only training "
        "(fast, use for a quick CPU smoke-test run, but won't reach the "
        "proposal's 80%% accuracy target on its own).",
    )
    parser.add_argument(
        "--fine-tune-epochs",
        type=int,
        default=15,
        help="After the frozen phase, unfreeze the backbone and continue training "
        "at --fine-tune-lr for this many epochs. Set 0 to skip. This is the slow "
        "part on CPU -- move to a GPU (Colab) if it's impractical.",
    )
    parser.add_argument("--fine-tune-lr", type=float, default=1e-5)
    parser.add_argument(
        "--fine-tune-unfreeze-layers",
        type=int,
        default=30,
        help="Only unfreeze the last N layers of EfficientNetB0 (roughly its last "
        "block) instead of the whole 237-layer backbone. With only ~2,856 training "
        "images across 87 classes, fully unfreezing overfits/destabilizes fast.",
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

    # No manual rescaling here: EfficientNetB0 includes its own preprocessing
    # (a Rescaling layer) and expects raw [0, 255] float pixels as input.
    # Normalizing to [0, 1] ourselves on top of that double-shrinks the
    # signal and the model never learns (loss stays flat at ln(num_classes)).
    train_ds = train_ds.prefetch(tf.data.AUTOTUNE)
    if val_ds is not None:
        val_ds_eval = val_ds
        val_ds = val_ds.prefetch(tf.data.AUTOTUNE)

    model, base_model = build_model(num_classes)
    model.summary()

    callbacks = [
        tf.keras.callbacks.EarlyStopping(monitor="val_loss" if val_ds else "loss", patience=4, restore_best_weights=True),
        tf.keras.callbacks.ReduceLROnPlateau(monitor="val_loss" if val_ds else "loss", factor=0.5, patience=2),
    ]

    print(f"\n=== Phase 1: frozen backbone, {args.epochs} epochs ===")
    history = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=args.epochs,
        callbacks=callbacks,
    )
    combined_history = {k: list(v) for k, v in history.history.items()}

    # Phase 1's EarlyStopping(restore_best_weights=True) already leaves
    # `model` holding phase 1's own best-val_loss weights. Snapshot those
    # (and the val_loss they achieved) so that if fine-tuning regresses --
    # a real risk with ~2,856 images across 87 classes -- we can fall back
    # to them instead of silently shipping a worse model than phase 1 alone.
    phase1_weights = model.get_weights()
    phase1_best_val_loss = min(history.history.get("val_loss", history.history["loss"]))

    if not args.freeze_base and args.fine_tune_epochs > 0:
        n = args.fine_tune_unfreeze_layers
        print(f"\n=== Phase 2: fine-tuning last {n} layers, {args.fine_tune_epochs} epochs at lr={args.fine_tune_lr} ===")
        base_model.trainable = True
        if n > 0:
            for layer in base_model.layers[:-n]:
                layer.trainable = False
        model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=args.fine_tune_lr),
            loss="categorical_crossentropy",
            metrics=["accuracy"],
        )
        fine_tune_history = model.fit(
            train_ds,
            validation_data=val_ds,
            epochs=args.fine_tune_epochs,
            callbacks=callbacks,
        )
        for k, v in fine_tune_history.history.items():
            combined_history.setdefault(k, []).extend(v)

        phase2_best_val_loss = min(
            fine_tune_history.history.get("val_loss", fine_tune_history.history["loss"])
        )
        if phase2_best_val_loss > phase1_best_val_loss:
            print(
                f"Fine-tuning did not beat phase 1 (val_loss {phase2_best_val_loss:.4f} "
                f"vs {phase1_best_val_loss:.4f}) -- keeping phase 1's weights instead."
            )
            model.set_weights(phase1_weights)

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
        axes[0].plot(combined_history["accuracy"], label="train")
        if "val_accuracy" in combined_history:
            axes[0].plot(combined_history["val_accuracy"], label="val")
        if not args.freeze_base and args.fine_tune_epochs > 0:
            axes[0].axvline(args.epochs - 1, color="gray", linestyle="--", label="fine-tune starts")
        axes[0].set_title("Accuracy")
        axes[0].legend()

        axes[1].plot(combined_history["loss"], label="train")
        if "val_loss" in combined_history:
            axes[1].plot(combined_history["val_loss"], label="val")
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
            preds = model.predict(batch_x, verbose=0)
            y_true.extend(np.argmax(batch_y.numpy(), axis=1))
            y_pred.extend(np.argmax(preds, axis=1))

        report = classification_report(y_true, y_pred, target_names=class_names, zero_division=0)
        report_path = REPORTS_DIR / "cnn_classification_report.txt"
        report_path.write_text(report, encoding="utf-8")
        print(report)
        print(f"Saved classification report -> {report_path}")


if __name__ == "__main__":
    main()
