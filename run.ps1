# Local run: creates venv on first use, then starts the app at http://localhost:8000
if (-not (Test-Path .venv)) { python -m venv .venv; .\.venv\Scripts\pip install -r requirements.txt }
if (-not (Test-Path .env)) { Copy-Item .env.example .env; Write-Host "Made .env - put your GEMINI_API_KEY in it." }
.\.venv\Scripts\python -m uvicorn app.main:app --port 8000
