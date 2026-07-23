from dataclasses import dataclass
from typing import Callable, Any
from .llm_client import LLMClient
from .tool_registry import ToolRegistry
from .session import SessionManager
from .parser import ToolCallParser
from .tool_executor import ToolExecutor
from .stream_handler import StreamHandler
from .prompts import build_system_prompt
from config import Settings

@dataclass
class AgentResponse:
    text: str
    artifacts: dict[str, str]
    tools_called: list[str]

class Agent:
    def __init__(self, llm_client: LLMClient, tool_registry: ToolRegistry,
                 session_manager: SessionManager, parser: ToolCallParser,
                 settings: Settings):
        self.llm_client = llm_client
        self.tool_registry = tool_registry
        self.session_manager = session_manager
        self.parser = parser
        self.settings = settings
        self.tool_executor = ToolExecutor(tool_registry, session_manager)
    
    def handle_message(self, session_id: str, user_message: str,
                       status_callback: Callable[[str], None] | None = None,
                       stream_callback: Callable[[str], None] | None = None) -> AgentResponse:
        """Process user message through the ReAct agent loop."""
        
        # 1. Update history
        self.session_manager.add_to_history(session_id, "user", user_message)
        
        session_data = self.session_manager.get_session(session_id)
        
        # Prepare system prompt
        tools = self.tool_registry.get_all()
        system_prompt = build_system_prompt(session_data.__dict__, tools)
        
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(session_data.conversation_history)
        
        tools_called = []
        final_text = ""
        
        # Loop max 5 times for tool calls
        for _ in range(5):
            stream_handler = StreamHandler(self.parser, stream_callback)
            token_stream = self.llm_client.stream(messages)
            
            full_text, parse_result = stream_handler.process_stream(token_stream, is_final=False)
            messages.append({"role": "assistant", "content": full_text})
            
            if parse_result.has_tool_call and parse_result.tool_name:
                tool_name = parse_result.tool_name
                tool_args = parse_result.tool_args or {}
                
                if status_callback:
                    status_callback(f"Running {tool_name}...")
                    
                tools_called.append(tool_name)
                
                # Execute tool
                result = self.tool_executor.execute(session_id, tool_name, tool_args)
                
                obs_content = f"OBSERVATION ({tool_name}):\n{result.summary}"
                messages.append({"role": "user", "content": obs_content})
                
                # Reload session data after tool execution
                session_data = self.session_manager.get_session(session_id)
                # We could potentially update the system prompt here if context changes drastically
            else:
                # No tool call, final response
                final_text = full_text
                if stream_callback:
                    stream_callback(final_text)
                break
                
        self.session_manager.add_to_history(session_id, "assistant", final_text)
        
        return AgentResponse(
            text=final_text,
            artifacts=session_data.artifacts,
            tools_called=tools_called
        )
