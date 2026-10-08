from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from typing import Any

import httpx


_RETRYABLE = {429, 500, 502, 503, 504}


@dataclass
class OpenAICompatClient:
    base_url: str
    api_key: str
    model: str
    timeout_s: float = 120.0
    max_tokens: int = 256
    max_attempts: int = 10
    last_metadata: dict[str, Any] = field(default_factory=dict, init=False)

    @classmethod
    def from_env(cls, prefix: str = "OPENAI_COMPAT") -> "OpenAICompatClient":
        base_url = os.environ[f"{prefix}_BASE_URL"].rstrip("/")
        api_key = os.environ[f"{prefix}_API_KEY"]
        model = os.environ[f"{prefix}_MODEL"]
        return cls(base_url=base_url, api_key=api_key, model=model)

    def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.0,
        seed: int | None = None,
    ) -> str:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": self.max_tokens,
        }
        if seed is not None:
            payload["seed"] = seed

        last_error: Exception | None = None
        for attempt in range(1, self.max_attempts + 1):
            try:
                with httpx.Client(timeout=self.timeout_s) as client:
                    response = client.post(
                        f"{self.base_url}/chat/completions",
                        headers={"Authorization": f"Bearer {self.api_key}"},
                        json=payload,
                    )
                if response.status_code in _RETRYABLE:
                    retry_after = response.headers.get("retry-after")
                    if retry_after:
                        try:
                            delay = max(1.0, float(retry_after))
                        except ValueError:
                            delay = min(120.0, 5.0 * (2 ** (attempt - 1)))
                    else:
                        delay = min(120.0, 5.0 * (2 ** (attempt - 1)))
                    if attempt == self.max_attempts:
                        response.raise_for_status()
                    print(
                        f"Retryable OpenRouter HTTP {response.status_code}; "
                        f"attempt {attempt}/{self.max_attempts}, sleeping {delay:.1f}s",
                        flush=True,
                    )
                    time.sleep(delay)
                    continue

                response.raise_for_status()
                body = response.json()
                self.last_metadata = {
                    "response_id": body.get("id"),
                    "resolved_model": body.get("model"),
                    "provider": body.get("provider"),
                    "created": body.get("created"),
                    "usage": body.get("usage"),
                }
                return body["choices"][0]["message"]["content"]
            except (httpx.TransportError, httpx.TimeoutException) as exc:
                last_error = exc
                if attempt == self.max_attempts:
                    raise
                delay = min(120.0, 5.0 * (2 ** (attempt - 1)))
                print(
                    f"Retryable OpenRouter transport error; attempt "
                    f"{attempt}/{self.max_attempts}, sleeping {delay:.1f}s: {exc}",
                    flush=True,
                )
                time.sleep(delay)

        if last_error is not None:
            raise last_error
        raise RuntimeError("OpenRouter request failed without a terminal response")
