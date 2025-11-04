from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

class ComponentCreate(BaseModel):
    name: str
    description: str
    knowledge_name: str

class RefineRequest(BaseModel):
    refinement: str

class ComponentVersionOut(BaseModel):
    version: int
    code: str
    chat_history: Optional[List[Dict[str, Any]]]
    created_at: Optional[datetime]

    model_config = {"from_attributes": True}

class ComponentOut(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    knowledge_base_id: UUID
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    versions: Optional[List[ComponentVersionOut]]

    model_config = {"from_attributes": True}