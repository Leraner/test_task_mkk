import os
import random
import uuid
from pathlib import Path
from typing import ClassVar

from locust import FastHttpUser, between, task

# /flaky отвечает 500 на 10% запросов, чтобы под нагрузкой работали retry-очереди.
WEBHOOK_URL = os.getenv("LOAD_WEBHOOK_URL", "http://webhook-sink:8080/flaky")


def api_key() -> str:
    """API_KEY из окружения, иначе из .env в корне проекта."""
    if key := os.getenv("API_KEY"):
        return key
    env_file = Path(__file__).resolve().parents[2] / ".env"
    for line in env_file.read_text().splitlines():
        name, _, value = line.partition("=")
        if name.strip() == "API_KEY":
            return value.strip()
    raise RuntimeError("API_KEY не найден ни в окружении, ни в .env")


def payment_body() -> dict:
    return {
        "amount": f"{random.randint(1, 100_000)}.{random.randint(0, 99):02d}",
        "currency": random.choice(["RUB", "USD", "EUR"]),
        "description": "load test",
        "metadata": {"source": "locust"},
        "webhook_url": WEBHOOK_URL,
    }


class PaymentsUser(FastHttpUser):
    wait_time = between(0.1, 0.5)
    default_headers: ClassVar[dict[str, str]] = {"X-API-Key": api_key()}

    def on_start(self) -> None:
        self.created: list[tuple[str, dict, str]] = []

    @task(5)
    def create_payment(self) -> None:
        key = str(uuid.uuid4())
        body = payment_body()
        with self.client.post(
            "/api/v1/payments",
            json=body,
            headers={"Idempotency-Key": key},
            name="POST /api/v1/payments",
            catch_response=True,
        ) as response:
            if response.status_code != 202:
                response.failure(f"expected 202, got {response.status_code}")
                return
            self.created.append((key, body, response.json()["data"]["payment_id"]))

    @task(3)
    def get_payment(self) -> None:
        if not self.created:
            return
        _, _, payment_id = random.choice(self.created)
        self.client.get(
            f"/api/v1/payments/{payment_id}",
            name="GET /api/v1/payments/{payment_id}",
        )

    @task(1)
    def repeat_payment(self) -> None:
        """Повтор с тем же ключом и телом должен вернуть тот же payment_id."""
        if not self.created:
            return
        key, body, payment_id = random.choice(self.created)
        with self.client.post(
            "/api/v1/payments",
            json=body,
            headers={"Idempotency-Key": key},
            name="POST /api/v1/payments (repeat)",
            catch_response=True,
        ) as response:
            if response.status_code != 202:
                response.failure(f"expected 202, got {response.status_code}")
            elif response.json()["data"]["payment_id"] != payment_id:
                response.failure("repeat returned another payment_id")
