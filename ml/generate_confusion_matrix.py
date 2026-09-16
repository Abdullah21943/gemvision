"""Generate a confusion matrix + classification report for the trained
gemstone CNN, evaluated on the held-out test set.

Produces (into ml/reports/):
    cnn_confusion_matrix.png       -- full 87x87 heatmap
    cnn_confusion_matrix_top20.png -- the 20 most-confused classes only,
                                      more readable for a report body
    cnn_classification_report.txt  -- per-class precision/recall/F1 (re-generated,
                                      should match the numbers already reported)

Usage:
    backend/.venv/Scripts/python.exe ml/generate_confusion_matrix.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

ML_DIR = Path(__file__).resolve().parent
DATA_DIR = ML_DIR / "data" / "gemstones-images" / "test"
MODEL_PATH = ML_DIR.parent / "backend" / "models" / "gemstone_cnn.keras"
CLASS_INDICES_PATH = ML_DIR.parent / "backend" / "models" / "class_indices.json"
REPORTS_DIR = ML_DIR / "reports"
IMAGE_SIZE = 224


def main() -> None:
    import tensorflow as tf
    from sklearn.metrics import ConfusionMatrixDisplay, classification_report, confusion_matrix

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    with open(CLASS_INDICES_PATH, "r", encoding="utf-8") as f:
        class_indices: dict[str, int] = json.load(f)
    class_names = [None] * len(class_indices)
    for name, idx in class_indices.items():
        class_names[idx] = name

    model = tf.keras.models.load_model(MODEL_PATH)

    test_ds = tf.keras.utils.image_dataset_from_directory(
        DATA_DIR,
        image_size=(IMAGE_SIZE, IMAGE_SIZE),
        batch_size=32,
        label_mode="categorical",
        shuffle=False,
    )
    # Sanity check: the directory's own class ordering must match class_indices.json,
    # since we index into class_names by integer label below.
    assert test_ds.class_names == class_names, (
        "Class order mismatch between the dataset directory and class_indices.json -- "
        "the confusion matrix labels would be wrong if these don't line up."
    )

    y_true, y_pred = [], []
    for batch_x, batch_y in test_ds:
        preds = model.predict(batch_x, verbose=0)
        y_true.extend(np.argmax(batch_y.numpy(), axis=1))
        y_pred.extend(np.argmax(preds, axis=1))
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)

    overall_accuracy = (y_true == y_pred).mean()
    print(f"Overall accuracy on {len(y_true)} test images: {overall_accuracy:.4f}")

    # --- classification report (re-generated, for cross-check against the
    # numbers already quoted in the reports) ---
    report = classification_report(y_true, y_pred, target_names=class_names, zero_division=0)
    (REPORTS_DIR / "cnn_classification_report.txt").write_text(report, encoding="utf-8")
    print(report)

    # --- full 87x87 confusion matrix ---
    cm = confusion_matrix(y_true, y_pred, labels=range(len(class_names)))

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(26, 26))
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=class_names)
    disp.plot(ax=ax, xticks_rotation=90, colorbar=True, cmap="Purples", values_format="d")
    ax.set_title(f"GemVision CNN -- Confusion Matrix (all 87 classes, test accuracy {overall_accuracy:.1%})")
    fig.tight_layout()
    fig.savefig(REPORTS_DIR / "cnn_confusion_matrix.png", dpi=150)
    plt.close(fig)
    print(f"Saved -> {REPORTS_DIR / 'cnn_confusion_matrix.png'}")

    # --- readable subset: the 20 classes with the most total misclassifications
    # (either as a source of errors or a magnet for other classes' errors) ---
    off_diagonal = cm.copy()
    np.fill_diagonal(off_diagonal, 0)
    confusion_score = off_diagonal.sum(axis=0) + off_diagonal.sum(axis=1)
    top20_idx = np.argsort(confusion_score)[::-1][:20]
    top20_idx_sorted = sorted(top20_idx)
    cm_top20 = cm[np.ix_(top20_idx_sorted, top20_idx_sorted)]
    top20_names = [class_names[i] for i in top20_idx_sorted]

    fig, ax = plt.subplots(figsize=(12, 12))
    disp = ConfusionMatrixDisplay(confusion_matrix=cm_top20, display_labels=top20_names)
    disp.plot(ax=ax, xticks_rotation=90, colorbar=True, cmap="Purples", values_format="d")
    ax.set_title("GemVision CNN -- 20 Most-Confused Classes (subset of the full matrix)")
    fig.tight_layout()
    fig.savefig(REPORTS_DIR / "cnn_confusion_matrix_top20.png", dpi=150)
    plt.close(fig)
    print(f"Saved -> {REPORTS_DIR / 'cnn_confusion_matrix_top20.png'}")


if __name__ == "__main__":
    main()
