from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from urllib.error import URLError
from urllib.request import urlopen

from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from app.config import load_environment
from app.main import app


class UnavailableConnection:
    async def __aenter__(self) -> None:
        raise SQLAlchemyError("database unavailable")

    async def __aexit__(self, *args: object) -> None:
        return None


class UnavailableEngine:
    def connect(self) -> UnavailableConnection:
        return UnavailableConnection()

    async def dispose(self) -> None:
        return None


class AvailableConnection:
    statement: object | None = None

    async def __aenter__(self) -> AvailableConnection:
        return self

    async def __aexit__(self, *args: object) -> None:
        return None

    async def execute(self, statement: object) -> None:
        self.statement = statement


class AvailableEngine:
    def __init__(self) -> None:
        self.connection = AvailableConnection()
        self.disposed = False

    def connect(self) -> AvailableConnection:
        return self.connection

    async def dispose(self) -> None:
        self.disposed = True


class AppTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_homepage_serves_application_shell(self) -> None:
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.headers["content-type"])
        self.assertIn("Fla Chess", response.text)
        self.assertIn('href="#/system"', response.text)
        self.assertIn('id="app-view"', response.text)
        self.assertIn('src="/static/app.js"', response.text)

    def test_static_frontend_modules_are_served(self) -> None:
        expected_assets = {
            "index.html": "Fla Chess",
            "styles.css": ".app-shell",
            "app.js": '"/api/health"',
            "api.js": "class ApiError",
            "router.js": "AbortController",
            "render.js": "pendingAction",
        }

        for asset, marker in expected_assets.items():
            with self.subTest(asset=asset):
                response = self.client.get(f"/static/{asset}")

                self.assertEqual(response.status_code, 200)
                self.assertIn(marker, response.text)

    def test_health_route_returns_ok(self) -> None:
        response = self.client.get("/api/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_frontend_smoke_error_path_returns_404_json(self) -> None:
        response = self.client.get("/api/frontend-smoke/missing")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"detail": "Not Found"})

    def test_missing_database_url_warns_and_app_starts(self) -> None:
        with patch.dict(os.environ, {"DATABASE_URL": ""}):
            with self.assertLogs("app.main", level="WARNING") as logs:
                with TestClient(app) as client:
                    response = client.get("/api/health")

        self.assertEqual(response.status_code, 200)
        self.assertIn("DATABASE_URL is not set", logs.output[0])

    def test_unavailable_database_warns_and_app_starts(self) -> None:
        with (
            patch.dict(
                os.environ,
                {"DATABASE_URL": "postgresql+asyncpg://user:password@localhost/db"},
            ),
            patch("app.main.create_async_engine", return_value=UnavailableEngine()),
            patch("app.main.async_sessionmaker", return_value=object()),
            self.assertLogs("app.main", level="WARNING") as logs,
        ):
            with TestClient(app) as client:
                response = client.get("/api/health")

        self.assertEqual(response.status_code, 200)
        self.assertIn("startup will continue", logs.output[0])

    def test_startup_checks_database_and_disposes_engine(self) -> None:
        engine = AvailableEngine()
        with (
            patch.dict(
                os.environ,
                {"DATABASE_URL": "postgresql+asyncpg://user:password@localhost/db"},
            ),
            patch("app.main.create_async_engine", return_value=engine),
            patch("app.main.async_sessionmaker", return_value=object()),
            self.assertNoLogs("app.main", level="WARNING"),
        ):
            with TestClient(app) as client:
                response = client.get("/api/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(str(engine.connection.statement), "SELECT 1")
        self.assertTrue(engine.disposed)

    def test_dotenv_loads_without_overriding_process_environment(self) -> None:
        with TemporaryDirectory() as temp_dir:
            env_file = Path(temp_dir) / ".env"
            env_file.write_text(
                "DATABASE_URL=from-dotenv\nDOTENV_TEST_VALUE=loaded\n",
                encoding="utf-8",
            )
            with patch.dict(
                os.environ,
                {"DATABASE_URL": "from-process", "DOTENV_TEST_VALUE": ""},
            ):
                os.environ.pop("DOTENV_TEST_VALUE")
                with patch("app.config._ENV_FILE", env_file):
                    load_environment()

                self.assertEqual(os.environ["DATABASE_URL"], "from-process")
                self.assertEqual(os.environ["DOTENV_TEST_VALUE"], "loaded")


class UvicornSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            port = listener.getsockname()[1]

        cls.base_url = f"http://127.0.0.1:{port}"
        cls.server = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "app.main:app",
                "--host",
                "127.0.0.1",
                "--port",
                str(port),
            ],
            cwd=Path(__file__).resolve().parents[1],
            env={**os.environ, "DATABASE_URL": ""},
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )

        cls.wait_until_ready()

    @classmethod
    def wait_until_ready(cls) -> None:
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            if cls.server.poll() is not None:
                output, _ = cls.server.communicate()
                raise RuntimeError(f"Uvicorn failed to start:\n{output}")
            try:
                with urlopen(f"{cls.base_url}/api/health", timeout=0.25) as response:
                    if response.status == 200:
                        return
            except URLError:
                time.sleep(0.1)

        cls.tearDownClass()
        raise RuntimeError("Uvicorn did not become ready within 10 seconds")

    @classmethod
    def tearDownClass(cls) -> None:
        if cls.server.poll() is None:
            cls.server.terminate()
            try:
                cls.server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                cls.server.kill()
                cls.server.wait(timeout=5)
        if cls.server.stdout is not None:
            cls.server.stdout.close()

    def test_uvicorn_serves_frontend_and_api_over_http(self) -> None:
        with urlopen(f"{self.base_url}/") as response:
            homepage = response.read().decode()
            self.assertEqual(response.status, 200)
            self.assertIn('id="app-view"', homepage)
            self.assertIn('href="#/system"', homepage)

        with urlopen(f"{self.base_url}/static/app.js") as response:
            self.assertEqual(response.status, 200)
            self.assertIn(b'"/api/health"', response.read())

        with urlopen(f"{self.base_url}/api/health") as response:
            self.assertEqual(response.status, 200)
            self.assertEqual(response.read(), b'{"status":"ok"}')


if __name__ == "__main__":
    unittest.main()
