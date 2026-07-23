from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

@dataclass
class StepResult:
    tool_name: str
    success: bool
    summary: str
    artifacts: dict[str, str] = field(default_factory=dict)  # {name: path}
    data_state_updates: dict[str, Any] = field(default_factory=dict)
    error: str | None = None

class BaseTool(ABC):
    name: str
    description: str
    parameters: dict  # JSON Schema-style parameter definitions
    requires: list[str]  # Tool names that must run first
    
    @abstractmethod
    def execute(self, session_data: dict, args: dict, **kwargs) -> StepResult:
        """Execute the tool. Override in subclasses."""
        ...
    
    def get_prompt_definition(self) -> str:
        """Render this tool's definition for the system prompt."""
        # Format: ### {name}\nDescription: ...\nParameters:\n  - param (type, optional/required): desc. Default: val\nRequires: ...
        lines = [f"### {self.name}"]
        lines.append(f"Description: {self.description}")
        if self.parameters:
            lines.append("Parameters:")
            for pname, pinfo in self.parameters.items():
                req = "required" if pinfo.get("required") else "optional"
                ptype = pinfo.get("type", "any")
                desc = pinfo.get("description", "")
                default = pinfo.get("default")
                line = f"  - {pname} ({ptype}, {req}): {desc}"
                if default is not None:
                    line += f" Default: {default}"
                lines.append(line)
        if self.requires:
            lines.append(f"Requires: {', '.join(self.requires)}")
        else:
            lines.append("Requires: none")
        return "\n".join(lines)
