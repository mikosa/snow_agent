import os
from pathlib import Path
from dataclasses import dataclass, field
from dotenv import load_dotenv

@dataclass
class Settings:
    data_dir: Path = field(default_factory=lambda: Path(os.getenv("DATA_DIR", "data")))
    db_path: Path = field(init=False)
    llm_base_url: str = field(default_factory=lambda: os.getenv("LLM_BASE_URL", "http://localhost:8000/v1/chat"))
    llm_api_key: str = field(default_factory=lambda: os.getenv("LLM_API_KEY", ""))
    llm_headers: dict = field(init=False)
    llm_model: str = field(default_factory=lambda: os.getenv("LLM_MODEL", "default"))
    llm_timeout: int = field(default_factory=lambda: int(os.getenv("LLM_TIMEOUT", "120")))
    llm_max_iterations: int = field(default_factory=lambda: int(os.getenv("LLM_MAX_ITERATIONS", "10")))
    embedding_model: str = field(default_factory=lambda: os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2"))
    embedding_batch_size: int = field(default_factory=lambda: int(os.getenv("EMBEDDING_BATCH_SIZE", "256")))
    default_max_clusters: int = field(default_factory=lambda: int(os.getenv("DEFAULT_MAX_CLUSTERS", "50")))
    page_title: str = "Operations Analysis Agent"
    page_icon: str = "⚙️"
    
    def __post_init__(self):
        self.db_path = self.data_dir / "ops_agent.db"
        self.llm_headers = {
            "Authorization": f"Bearer {self.llm_api_key}" if self.llm_api_key else "",
            "Content-Type": "application/json"
        }
        
        # Create necessary directories
        self.data_dir.mkdir(parents=True, exist_ok=True)
        (self.data_dir / "uploads").mkdir(parents=True, exist_ok=True)
        (self.data_dir / "artifacts").mkdir(parents=True, exist_ok=True)

_settings: Settings | None = None

def get_settings() -> Settings:
    global _settings
    if _settings is None:
        load_dotenv()
        _settings = Settings()
    return _settings
