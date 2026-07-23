import httpx
import json
from typing import Generator

class LLMClient:
    def __init__(self, base_url: str, headers: dict, model: str, timeout: int = 120, debug: bool = True):
        self.base_url = base_url
        self.headers = headers
        self.model = model
        self.timeout = timeout
        self.debug = debug
        self.client = httpx.Client(headers=self.headers, timeout=self.timeout, verify=False)
    
    def stream(self, messages: list[dict]) -> Generator[str, None, None]:
        """Stream tokens from the LLM API. Yields one token at a time."""
        payload = {"model": self.model, "messages": messages, "stream": True}
        
        if self.debug:
            print(f"\\n--- LLM DEBUG: STREAM REQUEST ---")
            print(f"URL: {self.base_url}")
            print(f"Headers: {self.headers}")
            print(f"Payload: {json.dumps(payload, indent=2)}")
            print(f"---------------------------------\\n")
            
        try:
            with self.client.stream("POST", self.base_url, json=payload) as response:
                if self.debug and response.status_code != 200:
                    print(f"LLM ERROR: HTTP {response.status_code}")
                    print(response.read().decode())
                
                response.raise_for_status()
                for line in response.iter_lines():
                    if line:
                        chunk = self._parse_sse_chunk(line)
                        if chunk:
                            yield chunk
        except httpx.HTTPError as e:
            if self.debug:
                print(f"LLM EXCEPTION: {str(e)}")
            yield f"Error connecting to LLM API: {str(e)}"
    
    def send(self, messages: list[dict]) -> str:
        """Non-streaming send. Returns complete response text."""
        payload = {"model": self.model, "messages": messages, "stream": False}
        
        if self.debug:
            print(f"\\n--- LLM DEBUG: SEND REQUEST ---")
            print(f"URL: {self.base_url}")
            print(f"Payload: {json.dumps(payload, indent=2)}")
            print(f"-------------------------------\\n")
            
        try:
            response = self.client.post(self.base_url, json=payload)
            if self.debug:
                print(f"LLM RESPONSE STATUS: {response.status_code}")
                print(f"LLM RESPONSE BODY: {response.text[:500]}...") # Print first 500 chars
            
            response.raise_for_status()
            data = response.json()
            return data.get("choices", [{}])[0].get("message", {}).get("content", "")
        except httpx.HTTPError as e:
            if self.debug:
                print(f"LLM EXCEPTION: {str(e)}")
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
