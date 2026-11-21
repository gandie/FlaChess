# Fla Chess

## Run locally

Install the project and its FastAPI/Uvicorn dependencies into the existing
virtual environment:

```powershell
.\venv\Scripts\python.exe -m pip install -e .
```

Start the development server from the repository root:

```powershell
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) for the hello-world page,
[http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health) for the
API health response, or [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
for the interactive API documentation.

## Run with Docker

Start the FastAPI application and PostgreSQL from the repository root:

```powershell
docker compose up --build
```

The application is available on
[http://127.0.0.1:8000](http://127.0.0.1:8000). PostgreSQL is published on port
`5432` with the development database `fla_chess`, user `fla_chess`, and password
`fla_chess`.