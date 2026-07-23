from typing import Any
from .base import BaseTool, StepResult

class LLMMessageTool(BaseTool):
    name = "llm_message"
    description = "Send a freeform prompt to the LLM for analysis, summarization, or Q&A about the current data. General-purpose tool."
    parameters = {
        "prompt": {"type": "string", "required": True, "description": "The question or instruction to send"},
        "context_data": {"type": "string", "required": False, "default": None, "description": "Additional data to include as context"}
    }
    requires = []

    def execute(self, session_data: dict, args: dict, **kwargs) -> StepResult:
        return StepResult(
            tool_name=self.name,
            success=True,
            summary="Processed freeform prompt.",
            data_state_updates={}
        )
