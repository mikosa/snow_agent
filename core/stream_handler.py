from typing import Generator, Tuple
from .parser import ToolCallParser, ParseResult

class StreamHandler:
    """Manages two-phase streaming for the agent loop.
    
    Phase 1 (tool-calling): Buffer all tokens, detect tool_call blocks.
    Phase 2 (final response): Stream tokens to UI callback.
    """
    def __init__(self, parser: ToolCallParser, stream_callback=None):
        self.parser = parser
        self.stream_callback = stream_callback
    
    def process_stream(self, token_stream: Generator[str, None, None],
                       is_final: bool = False) -> Tuple[str, ParseResult]:
        """Process a token stream.
        
        If is_final=True and no tool_call detected, streams tokens to callback.
        Returns (full_text, parse_result).
        """
        full_text = ""
        for token in token_stream:
            full_text += token
            # We could stream to UI here if we determine early it's not a tool call, 
            # but for simplicity we buffer and then parse
            
        parse_result = self.parser.parse(full_text)
        
        if is_final and not parse_result.has_tool_call and self.stream_callback:
            # Re-emit tokens to callback
            self.stream_callback(full_text)
            
        return full_text, parse_result
