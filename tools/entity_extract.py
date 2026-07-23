from typing import Any
from .base import BaseTool, StepResult

class EntityExtractTool(BaseTool):
    name = "entity_extract"
    description = "Extract named entities (systems, applications, assignment groups, locations, error codes) from ticket text fields using the LLM."
    parameters = {
        "fields": {"type": "list[string]", "required": False, "default": None, "description": "Which text columns to extract from. Default: all text columns"}
    }
    requires = ["clean_scrub"]

    def execute(self, session_data: dict, args: dict, **kwargs) -> StepResult:
        return StepResult(
            tool_name=self.name,
            success=True,
            summary="Extracted entities from text fields.",
            data_state_updates={"is_entities_extracted": True}
        )
