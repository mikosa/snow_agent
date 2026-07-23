from tools.base import BaseTool

class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, BaseTool] = {}
    
    def register(self, tool: BaseTool) -> None:
        self._tools[tool.name] = tool
        
    def get(self, name: str) -> BaseTool:
        return self._tools.get(name)
        
    def get_all(self) -> list[BaseTool]:
        return list(self._tools.values())
        
    def get_names(self) -> list[str]:
        return list(self._tools.keys())
        
    def has(self, name: str) -> bool:
        return name in self._tools
