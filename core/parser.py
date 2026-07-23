import re
import json
from dataclasses import dataclass

@dataclass
class ParseResult:
    has_tool_call: bool
    tool_name: str | None = None
    tool_args: dict | None = None
    text_before: str = ""
    text_after: str = ""
    raw_block: str = ""

class ToolCallParser:
    PATTERN = r"```tool_call\s*\n(\{.*?\})\s*\n```"
    
    def parse(self, text: str) -> ParseResult:
        """Parse a complete text for tool_call blocks."""
        match = re.search(self.PATTERN, text, re.DOTALL)
        if not match:
            return ParseResult(has_tool_call=False, text_before=text)
            
        json_str = match.group(1)
        raw_block = match.group(0)
        start, end = match.span()
        
        text_before = text[:start].strip()
        text_after = text[end:].strip()
        
        try:
            data = json.loads(json_str)
            tool_name = data.get("tool")
            tool_args = data.get("args", {})
            
            if not tool_name:
                return ParseResult(has_tool_call=True, text_before=text_before, 
                                   text_after=text_after, raw_block=raw_block)
                                   
            return ParseResult(
                has_tool_call=True,
                tool_name=tool_name,
                tool_args=tool_args,
                text_before=text_before,
                text_after=text_after,
                raw_block=raw_block
            )
        except json.JSONDecodeError:
            return ParseResult(
                has_tool_call=True,
                text_before=text_before,
                text_after=text_after,
                raw_block=raw_block
            )
        
    def validate_tool_call(self, tool_name: str, tool_args: dict, 
                           available_tools: list[str]) -> tuple[bool, str]:
        """Validate that the tool exists and args are reasonable."""
        if not tool_name:
            return False, "Missing tool name."
        if tool_name not in available_tools:
            return False, f"Tool '{tool_name}' not found."
        if not isinstance(tool_args, dict):
            return False, "Args must be a dictionary."
        return True, ""
