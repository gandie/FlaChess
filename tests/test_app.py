import socket
import subprocess
import sys
import time
import unittest
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

from fastapi.testclient import TestClient

from app.main import app


class AppTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_homepage_serves_static_hello_world(self) -> None:
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.headers["content-type"])
        self.assertIn("Hello, Fla Chess!", response.text)

    def test_static_frontend_files_are_served(self) -> None:
        response = self.client.get("/static/index.html")

        self.assertEqual(response.status_code, 200)
        self.assertIn("Hello, Fla Chess!", response.text)

    def test_health_route_returns_ok(self) -> None:
        response = self.client.get("/api/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})


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
            self.assertIn("Hello, Fla Chess!", homepage)

        with urlopen(f"{self.base_url}/static/index.html") as response:
            self.assertEqual(response.status, 200)

        with urlopen(f"{self.base_url}/api/health") as response:
            self.assertEqual(response.status, 200)
            self.assertEqual(response.read(), b'{"status":"ok"}')


if __name__ == "__main__":
    unittest.main()
