from __future__ import annotations

import os
from dataclasses import dataclass

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential


@dataclass
class OpenAICompatClient:
    base_url: str
    api_key: str
    model: str
    timeout_s: float = 120.0

    @classmethod
    def from_env(cls, prefix: str = "OPENAI_COMPAT") -> "OpenAICompatClient":
        base_url = os.environ[f"{prefix}_BASE_URL"].rstrip("/")
        api_key = os.environ[f"{prefix}_API_KEY"]
        model = os.environ[f"{prefix}_MODEL"]
        return cls(base_url=base_url, api_key=api_key, model=model)

    @retry(stop=stop_after_attempt(4), wait=wait_exponential(multiplier=1, min=1, max=20))
    def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.0,
        seed: int | None = None,
    ) -> str:
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        if seed is not None:
            payload["seed"] = seed
        with httpx.Client(timeout=self.timeout_s) as client:
            response = client.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=payload,
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
