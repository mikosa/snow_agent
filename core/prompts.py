from typing import Any, Dict
from tools.base import BaseTool
import json

def format_data_context(session_data: dict) -> str:
    """Builds the current data context section for the prompt."""
    data_state = session_data.get('data_state', {})
    
    # Handle data_state whether it's a dictionary or a dataclass
    if not isinstance(data_state, dict):
        data_state = getattr(data_state, '__dict__', {})

    row_count = data_state.get('row_count', 'Unknown')
    cols = data_state.get('column_names', [])
    cols_str = ', '.join(cols) if cols else 'None'
    
    context = f"## Current Data Context\n"
    context += f"- Uploaded Rows: {row_count}\n"
    context += f"- Columns: {cols_str}\n"
    
    steps = [
        ("Clean/Scrub", data_state.get('is_cleaned', False)),
        ("Entity Extraction", data_state.get('is_entities_extracted', False)),
        ("Embedding", data_state.get('is_embedded', False)),
        ("Clustering", data_state.get('is_clustered', False)),
        ("Categorization", data_state.get('is_categorized', False)),
        ("Subcategorization", data_state.get('is_subcategorized', False)),
    ]
    
    context += "- Processing Steps:\n"
    for name, done in steps:
        mark = "✓" if done else "✗"
        context += f"  - [{mark}] {name}\n"
        
    return context

def build_system_prompt(session_data: dict, tools: list[BaseTool]) -> str:
    """Dynamically builds the system prompt for the agent."""
    
    # 1. Role & Identity
    prompt = "You are an operations analysis agent that helps users explore, cluster, and categorize operational ticket data from CSV exports.\n\n"
    
    # 2. Available Tools
    prompt += "## Available Tools\n"
    for tool in tools:
        prompt += tool.get_prompt_definition() + "\n\n"
        
    # 3. Tool Calling Convention
    prompt += "## Tool Calling Convention\n"
    prompt += "To use a tool, respond with a single code block matching exactly this format:\n"
    prompt += "```tool_call\n"
    prompt += '{"tool": "tool_name", "args": {"arg1": "value1"}}\n'
    prompt += "```\n"
    prompt += "Produce ONE tool call per response. After execution, you will receive an OBSERVATION.\n\n"
    
    # 4. Current Data Context
    prompt += format_data_context(session_data) + "\n\n"
    
    # 5. Behavioral Guidelines
    prompt += "## Behavioral Guidelines\n"
    prompt += "- Always explain your actions before taking them.\n"
    prompt += "- Run prerequisite steps automatically if they haven't been completed.\n"
    prompt += "- Offer exports to the user after full analysis.\n"
    prompt += "- Be concise but informative.\n"
    
    return prompt
