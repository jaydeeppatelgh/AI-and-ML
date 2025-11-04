from sqlalchemy import Column, String, Text, ForeignKey, DateTime, func, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class KnowledgeBase(Base):
    __tablename__ = "knowledge_base"
    id = Column(UUID(as_uuid=True), primary_key=True)
    name = Column(String, unique=True, nullable=False)
    spec = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Component(Base):
    __tablename__ = "components"
    id = Column(UUID(as_uuid=True), primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    knowledge_base_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_base.id"), nullable=False)
    knowledge_base = relationship("KnowledgeBase")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class ComponentVersion(Base):
    __tablename__ = "component_versions"
    id = Column(UUID(as_uuid=True), primary_key=True)
    component_id = Column(UUID(as_uuid=True), ForeignKey("components.id"), nullable=False)
    version = Column(Integer, nullable=False)
    code = Column(Text, nullable=False)
    chat_history = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
