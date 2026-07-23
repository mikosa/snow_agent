from .base import BaseTool, StepResult
from .clean_scrub import CleanScrubTool
from .entity_extract import EntityExtractTool
from .embed_data import EmbedDataTool
from .agglom_cluster import AgglomClusterTool
from .llm_message import LLMMessageTool
from .category_cluster import CategoryClusterTool
from .subcategory_cluster import SubcategoryClusterTool

def register_all_tools(registry):
    registry.register(CleanScrubTool())
    registry.register(EntityExtractTool())
    registry.register(EmbedDataTool())
    registry.register(AgglomClusterTool())
    registry.register(LLMMessageTool())
    registry.register(CategoryClusterTool())
    registry.register(SubcategoryClusterTool())
