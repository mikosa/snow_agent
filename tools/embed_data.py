from typing import Any
from .base import BaseTool, StepResult

class EmbedDataTool(BaseTool):
    name = "embed_data"
    description = "Generate vector embeddings for the ticket text using sentence-transformers (runs locally, no LLM API call)."
    parameters = {
        "model": {"type": "string", "required": False, "default": "all-MiniLM-L6-v2", "description": "Embedding model name"},
        "batch_size": {"type": "int", "required": False, "default": 256, "description": "Batch size for encoding"}
    }
    requires = ["clean_scrub"]

    def execute(self, session_data: dict, args: dict, **kwargs) -> StepResult:
        return StepResult(
            tool_name=self.name,
            success=True,
            summary="Generated vector embeddings for the ticket text.",
            data_state_updates={"is_embedded": True}
        )
