import uuid
from dataclasses import dataclass, field
from datetime import datetime
from db.models import Session as SessionModel, DataState as DataStateModel, Conversation, Upload
from db.database import get_session

@dataclass 
class DataState:
    """In-memory representation of processing state."""
    is_cleaned: bool = False
    is_entities_extracted: bool = False
    is_embedded: bool = False
    is_clustered: bool = False
    cluster_count: int | None = None
    is_categorized: bool = False
    is_subcategorized: bool = False
    row_count: int | None = None
    column_names: list[str] = field(default_factory=list)

@dataclass
class SessionData:
    """Complete session state."""
    id: str
    name: str | None
    created_at: datetime
    uploads: list[dict]
    active_upload_id: str | None
    data_state: DataState
    conversation_history: list[dict]
    artifacts: dict[str, str]

class SessionManager:
    DOWNSTREAM_DEPS = {
        'clean_scrub': ['entity_extract', 'embed_data', 'agglom_cluster', 'category_cluster', 'subcategory_cluster'],
        'entity_extract': ['embed_data', 'agglom_cluster', 'category_cluster', 'subcategory_cluster'],
        'embed_data': ['agglom_cluster', 'category_cluster', 'subcategory_cluster'],
        'agglom_cluster': ['category_cluster', 'subcategory_cluster'],
        'category_cluster': ['subcategory_cluster']
    }

    def __init__(self, db_session_factory, file_store):
        self.db_session_factory = db_session_factory
        self.file_store = file_store
    
    def create_session(self, name: str | None = None) -> SessionData:
        session_id = str(uuid.uuid4())
        session_data = SessionData(
            id=session_id,
            name=name,
            created_at=datetime.utcnow(),
            uploads=[],
            active_upload_id=None,
            data_state=DataState(),
            conversation_history=[],
            artifacts={}
        )
        self._persist(session_data)
        return session_data

    def get_session(self, session_id: str) -> SessionData:
        return self._load(session_id)

    def list_sessions(self) -> list[dict]:
        with self.db_session_factory() as db:
            sessions = db.query(SessionModel).all()
            return [{"id": s.id, "name": s.name, "created_at": s.created_at, "updated_at": s.updated_at} for s in sessions]

    def add_upload(self, session_id: str, upload_info: dict) -> None:
        session_data = self.get_session(session_id)
        session_data.uploads.append(upload_info)
        session_data.active_upload_id = upload_info.get('id')
        self._persist(session_data)

    def add_to_history(self, session_id: str, role: str, content: str) -> None:
        session_data = self.get_session(session_id)
        session_data.conversation_history.append({"role": role, "content": content})
        self._persist(session_data)

    def update_data_state(self, session_id: str, updates: dict) -> None:
        session_data = self.get_session(session_id)
        for k, v in updates.items():
            if hasattr(session_data.data_state, k):
                setattr(session_data.data_state, k, v)
        self._persist(session_data)

    def update_artifacts(self, session_id: str, artifacts: dict) -> None:
        session_data = self.get_session(session_id)
        session_data.artifacts.update(artifacts)
        self._persist(session_data)

    def get_conversation_history(self, session_id: str) -> list[dict]:
        session_data = self.get_session(session_id)
        return session_data.conversation_history

    def invalidate_downstream(self, session_id: str, from_step: str) -> None:
        """When a tool re-runs, invalidate all downstream results."""
        if from_step not in self.DOWNSTREAM_DEPS:
            return
            
        updates = {}
        for step in self.DOWNSTREAM_DEPS[from_step]:
            if step == 'entity_extract':
                updates['is_entities_extracted'] = False
            elif step == 'embed_data':
                updates['is_embedded'] = False
            elif step == 'agglom_cluster':
                updates['is_clustered'] = False
            elif step == 'category_cluster':
                updates['is_categorized'] = False
            elif step == 'subcategory_cluster':
                updates['is_subcategorized'] = False
        
        self.update_data_state(session_id, updates)

    def _persist(self, session_data: SessionData) -> None:
        """Save session state to SQLite."""
        # Simplified implementation for now
        pass

    def _load(self, session_id: str) -> SessionData:
        """Load session state from SQLite."""
        # Simplified implementation for now
        # Ideally this reads from db_session_factory
        return SessionData(id=session_id, name="Temp", created_at=datetime.utcnow(), 
                           uploads=[], active_upload_id=None, data_state=DataState(), 
                           conversation_history=[], artifacts={})
