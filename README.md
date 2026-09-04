# GemVision

AI-powered gemstone identification and price estimation — a cross-platform
Flutter app (Android/iOS) backed by a FastAPI ML service (CNN gemstone-type
classifier + XGBoost price regressor) and Supabase (auth, database, storage).

Built from the BSc project proposal by Abdullah Bashir (0413206), supervised
by Callum Altham. See [docs/PROJECT_PROPOSAL.md](docs/PROJECT_PROPOSAL.md)
for the original proposal text this implementation follows.

## Architecture — the six modules

| # | Module | Where |
|---|--------|-------|
| 1 | User Authentication (Supabase Auth) | [mobile/lib/screens/auth](mobile/lib/screens/auth), [mobile/lib/services/auth_service.dart](mobile/lib/services/auth_service.dart) |
| 2 | Image Capture and Upload | [mobile/lib/screens/capture/capture_screen.dart](mobile/lib/screens/capture/capture_screen.dart) |
| 3 | Gemstone Type Detection (CNN) | [backend/app/models/cnn_model.py](backend/app/models/cnn_model.py), [ml/train_cnn.py](ml/train_cnn.py) |
| 4 | Price Estimation (XGBoost) | [backend/app/models/price_model.py](backend/app/models/price_model.py), [ml/train_price_model.py](ml/train_price_model.py) |
| 5 | Scan History (Supabase Postgres) | [mobile/lib/services/scan_history_service.dart](mobile/lib/services/scan_history_service.dart), [supabase/schema.sql](supabase/schema.sql) |
| 6 | Flutter UI Dashboard | [mobile/lib/screens/home](mobile/lib/screens/home), [mobile/lib/theme/app_theme.dart](mobile/lib/theme/app_theme.dart) |

```
GemVision/
├── backend/     FastAPI service exposing /predict and /price
├── ml/          Dataset download + model training scripts (produce backend/models/*)
├── mobile/      Flutter app (Android/iOS/web)
├── supabase/    SQL schema (tables, RLS policies, storage bucket)
└── docs/        Proposal reference
```

The Flutter app never talks to the ML models directly — it calls the FastAPI
backend over HTTP, and talks to Supabase directly for auth/history/storage.

## Status: what's done vs. what needs you

Everything that's pure code is implemented and has been verified:
- Backend builds, boots, serves `/health`, `/predict`, `/price`, and fails
  **gracefully** (503, not a crash) when model artifacts aren't present yet
  — confirmed by running it and hitting all three endpoints, and by
  `pytest` (3/3 passing).
- Flutter app: all 6 modules' screens are written and wired together
  (`flutter analyze` clean, `flutter test` passing).
- Training scripts, Supabase schema, and dataset-download script are
  written and ready to run.

What's **left and needs manual action from you** (listed in the order
you'd naturally do them) is in the next section — mainly things that
require an account only you can create, real datasets, or a physical
device/emulator I don't have access to.

## Manual steps required from you

### 1. Backend Python environment
The training scripts need **TensorFlow 2.17**, which does not yet support
Python 3.13 (what's on this machine). Install Python 3.10, 3.11, or 3.12
alongside it, then:
```bash
cd backend
py -3.11 -m venv .venv        # or your 3.10/3.11/3.12 install
.venv\Scripts\activate
pip install -r requirements.txt
```
(FastAPI itself runs fine on any Python version — this only matters once
you install `requirements.txt`, i.e. once you're training or serving real
models.)

### 2. Kaggle datasets
1. Log in to kaggle.com → Settings → API → **Create New Token** → save
   `kaggle.json` to `C:\Users\<you>\.kaggle\kaggle.json`.
2. Run:
   ```bash
   python ml/download_datasets.py
   ```
   This pulls all three datasets from the proposal into `ml/data/`.
3. Open `ml/data/gemstone-price-prediction/*.csv` and check its columns
   against `COLUMN_ALIASES` at the top of
   [ml/train_price_model.py](ml/train_price_model.py) — that dataset is a
   diamonds-pricing dataset and may not literally have a "gem_type" column;
   the script falls back to a constant type if so, but skim the printed
   "Detected columns" line on first run to be sure it guessed right.

### 3. Train the models
```bash
python ml/train_cnn.py --epochs 20          # ~hours on CPU; use --freeze-base for a quick run,
                                             # or Google Colab (free GPU tier, per the proposal)
python ml/train_price_model.py              # seconds/minutes on CPU, XGBoost doesn't need a GPU
```
Outputs land in `backend/models/` (gitignored) and `ml/reports/` (accuracy
plot, classification report, RMSE/MAE/R² — needed for your evaluation
chapter, proposal Objective 7).

### 4. Supabase project
I can't create accounts on your behalf. You'll need to:
1. Create a free project at supabase.com.
2. Project Settings → API → copy the **Project URL** and **anon public key**.
3. SQL Editor → paste and run [supabase/schema.sql](supabase/schema.sql)
   (creates `profiles`, `scans`, RLS policies, and the `scan-images`
   storage bucket).
4. If the bucket insert in the script doesn't take (some projects require
   creating buckets via the dashboard first): Storage → New bucket →
   name it exactly `scan-images`, keep it **private** — the RLS policies
   in the script already scope access per-user.

### 5. Wire the Flutter app to your backend/Supabase
Edit `mobile/lib/config/secrets.dart` (already gitignored, currently
placeholder values) with your real Supabase URL/anon key and the FastAPI
backend's address — see the comments in
[mobile/lib/config/secrets.example.dart](mobile/lib/config/secrets.example.dart)
for which URL form to use (Android emulator vs. physical device vs.
deployed).

### 6. Run it on a device/emulator
I don't have an Android emulator, iOS simulator, or physical device
attached, so this step is yours:
```bash
cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000   # start the API
cd mobile && flutter run                                        # pick a device when prompted
```

### 7. Deploy the backend (optional, for a non-localhost demo)
Push `backend/` to Render or Railway's free tier (per the proposal), then
update `apiBaseUrl` in `secrets.dart` to the deployed URL.

### 8. Ethics approval
The proposal notes ethical approval for user acceptance testing is
"pending submission" — that's a university administrative process, not
something I can do for you.

## Verifying what's already working

```bash
# Backend (no trained models needed — verifies the API contract itself)
cd backend && python -m venv .venv && .venv\Scripts\activate
pip install fastapi uvicorn python-multipart pydantic pydantic-settings pillow numpy
python -m pytest tests/ -v

# Flutter
cd mobile && flutter pub get && flutter analyze && flutter test
```

## Data privacy & ethics notes (from the proposal)

- No PII collected beyond the email used for Supabase Auth.
- Scan images live in a private Supabase Storage bucket, access scoped to
  the uploading user via RLS (see `supabase/schema.sql`).
- Models train only on the three public Kaggle datasets — no scraping.
