"""Download the three Kaggle datasets referenced in the project proposal.

Requires a Kaggle API token. This is a MANUAL, one-time setup step:
  1. Log in to kaggle.com -> Settings -> API -> "Create New Token".
  2. Save the downloaded kaggle.json to:
       Windows:  C:\\Users\\<you>\\.kaggle\\kaggle.json
       macOS/Linux: ~/.kaggle/kaggle.json
     (or set KAGGLE_USERNAME / KAGGLE_KEY environment variables instead)
  3. pip install -r backend/requirements.txt   (includes the kaggle package)

Usage:
    python ml/download_datasets.py
"""

from __future__ import annotations

import zipfile
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"

DATASETS = {
    "gemstones-images": "lsind18/gemstones-images",
    "gemstone-price-prediction": "colearninglounge/gemstone-price-prediction",
    "precious-gemstone-identification": "gauravkamath02/precious-gemstone-identification",
}


def main() -> None:
    try:
        from kaggle.api.kaggle_api_extended import KaggleApi
    except OSError as exc:
        raise SystemExit(
            "Kaggle API credentials not found. Place kaggle.json in ~/.kaggle/ "
            "(see the docstring at the top of this script) and re-run."
        ) from exc

    api = KaggleApi()
    api.authenticate()

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    for folder_name, dataset_slug in DATASETS.items():
        target_dir = DATA_DIR / folder_name
        # Re-running this script shouldn't re-download multi-GB datasets
        # that are already present (the third dataset alone is ~7.7GB).
        if target_dir.exists() and any(target_dir.iterdir()):
            print(f"[skip] {folder_name} already downloaded at {target_dir}")
            continue

        print(f"[download] {dataset_slug} -> {target_dir}")
        target_dir.mkdir(parents=True, exist_ok=True)
        api.dataset_download_files(dataset_slug, path=str(target_dir), unzip=False, quiet=False)

        # Kaggle always hands back a single zip per dataset; extract then
        # discard it so ml/data/ only holds the files training actually reads.
        for zip_path in target_dir.glob("*.zip"):
            print(f"[unzip] {zip_path.name}")
            with zipfile.ZipFile(zip_path) as zf:
                zf.extractall(target_dir)
            zip_path.unlink()

    print("\nDone. Inspect ml/data/*/ and adjust column/folder names in "
          "ml/train_cnn.py / ml/train_price_model.py if the dataset layout "
          "differs from what's assumed there.")


if __name__ == "__main__":
    main()
