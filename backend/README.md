# PhoenixML Backend

This backend provides the demo API and static UI for the PhoenixML project.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Update the values in `.env` before production use.

## Run locally

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Demo login

- Username: `admin`
- Password: `admin123`

## API endpoints

- `GET /` 
- `GET /health`
- `POST /api/register`
- `POST /api/login`
- `GET /api/me`
- `GET /api/models`
- `POST /api/models`
- `POST /api/models/{model_id}/monitoring`
- `GET /api/models/{model_id}/monitoring`
- `GET /api/dashboard`

Open docs at: `http://localhost:8000/docs`
