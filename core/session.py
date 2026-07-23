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
        import json
        with self.db_session_factory() as db:
            session_model = db.query(SessionModel).filter_by(id=session_data.id).first()
            if not session_model:
                session_model = SessionModel(id=session_data.id, name=session_data.name)
                db.add(session_model)
                
            # Update DataState
            ds_model = session_model.data_state
            if not ds_model:
                ds_model = DataStateModel(session_id=session_data.id)
                session_model.data_state = ds_model
                
            ds_model.active_upload_id = session_data.active_upload_id
            ds_model.is_cleaned = session_data.data_state.is_cleaned
            ds_model.is_entities_extracted = session_data.data_state.is_entities_extracted
            ds_model.is_embedded = session_data.data_state.is_embedded
            ds_model.is_clustered = session_data.data_state.is_clustered
            ds_model.cluster_count = session_data.data_state.cluster_count
            ds_model.is_categorized = session_data.data_state.is_categorized
            ds_model.is_subcategorized = session_data.data_state.is_subcategorized
            ds_model.artifacts_json = json.dumps(session_data.artifacts)
            
            # Sync conversation history
            # For simplicity, we just clear and rewrite the history 
            # if we are doing full persist (since it's small)
            # A more optimal approach is to only insert new ones, but this guarantees consistency
            db.query(Conversation).filter_by(session_id=session_data.id).delete()
            for msg in session_data.conversation_history:
                db.add(Conversation(
                    session_id=session_data.id,
                    role=msg["role"],
                    content=msg["content"]
                ))
            db.commit()

    def _load(self, session_id: str) -> SessionData:
        """Load session state from SQLite."""
        import json
        with self.db_session_factory() as db:
            session_model = db.query(SessionModel).filter_by(id=session_id).first()
            if not session_model:
                # Fallback if somehow not created yet
                return SessionData(id=session_id, name="Temp", created_at=datetime.utcnow(), 
                                   uploads=[], active_upload_id=None, data_state=DataState(), 
                                   conversation_history=[], artifacts={})
            
            ds_model = session_model.data_state
            if ds_model:
                data_state = DataState(
                    is_cleaned=ds_model.is_cleaned,
                    is_entities_extracted=ds_model.is_entities_extracted,
                    is_embedded=ds_model.is_embedded,
                    is_clustered=ds_model.is_clustered,
                    cluster_count=ds_model.cluster_count,
                    is_categorized=ds_model.is_categorized,
                    is_subcategorized=ds_model.is_subcategorized
                )
                artifacts = json.loads(ds_model.artifacts_json) if ds_model.artifacts_json else {}
                active_upload_id = ds_model.active_upload_id
            else:
                data_state = DataState()
                artifacts = {}
                active_upload_id = None
                
            uploads = []
            for u in session_model.uploads:
                uploads.append({
                    "id": u.id, "filename": u.filename, "file_path": u.file_path,
                    "row_count": u.row_count, "columns_json": u.columns_json,
                    "file_size_bytes": u.file_size_bytes
                })
                
            conv_history = [{"role": c.role, "content": c.content} 
                            for c in sorted(session_model.conversations, key=lambda x: x.id)]
                            
            return SessionData(
                id=session_id,
                name=session_model.name,
                created_at=session_model.created_at,
                uploads=uploads,
                active_upload_id=active_upload_id,
                data_state=data_state,
                conversation_history=conv_history,
                artifacts=artifacts
            )
