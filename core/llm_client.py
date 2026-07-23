import httpx
import json
from typing import Generator

class LLMClient:
    def __init__(self, base_url: str, headers: dict, timeout: int = 120):
        self.base_url = base_url
        self.headers = headers
        self.timeout = timeout
        self.client = httpx.Client(headers=self.headers, timeout=self.timeout)
    
    def stream(self, messages: list[dict]) -> Generator[str, None, None]:
        """Stream tokens from the LLM API. Yields one token at a time."""
        payload = {"messages": messages, "stream": True}
        try:
            with self.client.stream("POST", self.base_url, json=payload) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if line:
                        chunk = self._parse_sse_chunk(line)
                        if chunk:
                            yield chunk
        except httpx.HTTPError as e:
            yield f"Error connecting to LLM API: {str(e)}"
    
    def send(self, messages: list[dict]) -> str:
        """Non-streaming send. Returns complete response text."""
        payload = {"messages": messages, "stream": False}
        try:
            response = self.client.post(self.base_url, json=payload)
            response.raise_for_status()
            data = response.json()
            return data.get("choices", [{}])[0].get("message", {}).get("content", "")
        except httpx.HTTPError as e:
            return f"Error: {str(e)}"
    
    def _parse_sse_chunk(self, chunk: str) -> str | None:
        """Parse an SSE chunk. Returns extracted text or None."""
        if chunk.startswith("data: "):
            data_str = chunk[6:]
            if data_str.strip() == "[DONE]":
                return None
            try:
                data = json.loads(data_str)
                return data.get("choices", [{}])[0].get("delta", {}).get("content", "")
            except json.JSONDecodeError:
                return None
        return None
