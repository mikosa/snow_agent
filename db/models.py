import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

def _generate_uuid():
    return str(uuid.uuid4())

class Session(Base):
    __tablename__ = "sessions"
    
    id = Column(String, primary_key=True, default=_generate_uuid)
    name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    uploads = relationship("Upload", back_populates="session", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="session", cascade="all, delete-orphan")
    category_results = relationship("CategoryResult", back_populates="session", cascade="all, delete-orphan")
    data_state = relationship("DataState", uselist=False, back_populates="session", cascade="all, delete-orphan")

class Upload(Base):
    __tablename__ = "uploads"
    
    id = Column(String, primary_key=True, default=_generate_uuid)
    session_id = Column(String, ForeignKey("sessions.id"))
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    row_count = Column(Integer)
    columns_json = Column(Text)
    file_size_bytes = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    session = relationship("Session", back_populates="uploads")

class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, ForeignKey("sessions.id"))
    role = Column(String)  # user | assistant | tool
    content = Column(Text)
    tool_calls_json = Column(Text, nullable=True)
    tool_name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    session = relationship("Session", back_populates="conversations")

class DataState(Base):
    __tablename__ = "data_states"
    
    session_id = Column(String, ForeignKey("sessions.id"), primary_key=True)
    active_upload_id = Column(String, ForeignKey("uploads.id"), nullable=True)
    is_cleaned = Column(Boolean, default=False)
    is_entities_extracted = Column(Boolean, default=False)
    is_embedded = Column(Boolean, default=False)
    is_clustered = Column(Boolean, default=False)
    cluster_count = Column(Integer, nullable=True)
    is_categorized = Column(Boolean, default=False)
    is_subcategorized = Column(Boolean, default=False)
    artifacts_json = Column(Text, default="{}")
    
    session = relationship("Session", back_populates="data_state")

class CategoryResult(Base):
    __tablename__ = "category_results"
    
    id = Column(String, primary_key=True, default=_generate_uuid)
    session_id = Column(String, ForeignKey("sessions.id"))
    cluster_id = Column(Integer)
    category_name = Column(String)
    subcategory_name = Column(String, nullable=True)
    ticket_count = Column(Integer)
    representative_tickets_json = Column(Text)
    llm_reasoning = Column(Text)
    
    session = relationship("Session", back_populates="category_results")
