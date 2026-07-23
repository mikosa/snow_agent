import shutil
from pathlib import Path

class FileStore:
    """Manages files and artifacts for the Operations Analysis Agent."""
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.uploads_dir = self.data_dir / "uploads"
        self.artifacts_dir = self.data_dir / "artifacts"
        
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.uploads_dir.mkdir(parents=True, exist_ok=True)
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        
    def save_upload(self, upload_id: str, file_data: bytes, filename: str) -> Path:
        """Saves an uploaded file to the uploads directory."""
        # Using upload_id to prevent naming collisions
        file_path = self.uploads_dir / f"{upload_id}_{filename}"
        with open(file_path, "wb") as f:
            f.write(file_data)
        return file_path
        
    def get_upload_path(self, upload_id: str) -> Path:
        """Finds the path for a specific upload id."""
        # Finds the first matching file that starts with upload_id
        for file_path in self.uploads_dir.iterdir():
            if file_path.is_file() and file_path.name.startswith(f"{upload_id}_"):
                return file_path
        raise FileNotFoundError(f"Upload with ID {upload_id} not found.")

    def get_artifacts_dir(self, session_id: str) -> Path:
        """Gets or creates the artifact directory for a session."""
        session_dir = self.artifacts_dir / session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        return session_dir
        
    def get_exports_dir(self, session_id: str) -> Path:
        """Gets or creates the exports directory within a session's artifacts."""
        exports_dir = self.get_artifacts_dir(session_id) / "exports"
        exports_dir.mkdir(parents=True, exist_ok=True)
        return exports_dir
        
    def save_artifact(self, session_id: str, filename: str, data: bytes | str) -> Path:
        """Saves an artifact (file) for a specific session."""
        session_dir = self.get_artifacts_dir(session_id)
        file_path = session_dir / filename
        
        if isinstance(data, str):
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(data)
        else:
            with open(file_path, "wb") as f:
                f.write(data)
                
        return file_path
        
    def load_artifact(self, session_id: str, filename: str) -> Path:
        """Returns the path to an artifact, raising an error if it doesn't exist."""
        file_path = self.get_artifacts_dir(session_id) / filename
        if not file_path.exists():
            raise FileNotFoundError(f"Artifact {filename} for session {session_id} not found.")
        return file_path
        
    def artifact_exists(self, session_id: str, filename: str) -> bool:
        """Checks if an artifact exists for a session."""
        file_path = self.get_artifacts_dir(session_id) / filename
        return file_path.exists()
        
    def delete_session_artifacts(self, session_id: str):
        """Deletes all artifacts associated with a session."""
        session_dir = self.artifacts_dir / session_id
        if session_dir.exists() and session_dir.is_dir():
            shutil.rmtree(session_dir)
            
    def get_artifact_path(self, session_id: str, filename: str) -> Path:
        """Gets the path for an artifact without checking if it exists."""
        return self.get_artifacts_dir(session_id) / filename
