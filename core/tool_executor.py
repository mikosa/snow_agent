from .tool_registry import ToolRegistry
from .session import SessionManager, SessionData
from tools.base import BaseTool, StepResult

class ToolExecutor:
    def __init__(self, tool_registry: ToolRegistry, session_manager: SessionManager):
        self.tool_registry = tool_registry
        self.session_manager = session_manager
    
    def execute(self, session_id: str, tool_name: str, tool_args: dict) -> StepResult:
        """Look up tool, validate prerequisites, execute, update session."""
        tool = self.tool_registry.get(tool_name)
        if not tool:
            return StepResult(success=False, summary=f"Tool {tool_name} not found.")
            
        session_data = self.session_manager.get_session(session_id)
        
        ok, reason = self._check_prerequisites(tool, session_data)
        if not ok:
            return StepResult(success=False, summary=f"Prerequisites not met: {reason}")
            
        try:
            result = tool.execute(vars(session_data), tool_args)
            return result
        except Exception as e:
            return StepResult(success=False, summary=f"Execution error: {str(e)}")
    
    def _check_prerequisites(self, tool: BaseTool, session_data: SessionData) -> tuple[bool, str]:
        """Check if tool's required previous steps are completed."""
        state = session_data.data_state
        reqs = tool.required_data_state or []
        
        for req in reqs:
            if not getattr(state, req, False):
                return False, f"Missing required state: {req}"
                
        return True, ""
