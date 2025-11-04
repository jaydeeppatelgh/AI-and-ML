from sqlalchemy.orm import Session
from . import models
import uuid
from sqlalchemy import select, func

def get_knowledge_by_name(session: Session, name: str):
    return session.execute(select(models.KnowledgeBase).where(models.KnowledgeBase.name == name)).scalars().first()

def create_component_with_version(session: Session, name: str, description: str, kb_id, code: str, chat_history=None):
    comp = models.Component(id=uuid.uuid4(), name=name, description=description, knowledge_base_id=kb_id)
    session.add(comp)
    session.flush()
    ver = models.ComponentVersion(id=uuid.uuid4(), component_id=comp.id, version=1, code=code, chat_history=chat_history)
    session.add(ver)
    session.commit()
    return get_component(session, comp.id)

def get_component(session: Session, component_id):
    comp = session.execute(select(models.Component).where(models.Component.id == component_id)).scalars().first()
    if not comp:
        return None
    # fetch versions
    versions = session.execute(select(models.ComponentVersion).where(models.ComponentVersion.component_id == comp.id).order_by(models.ComponentVersion.version)).scalars().all()
    comp.versions = [{"version": v.version, "code": v.code, "chat_history": v.chat_history, "created_at": v.created_at.isoformat()} for v in versions]
    return comp

def get_component_versions(session: Session, component_id):
    comp = get_component(session, component_id)
    if not comp:
        return None
    return comp.versions

def get_latest_chat_history(session: Session, comp_id):
    v = session.execute(select(models.ComponentVersion).where(models.ComponentVersion.component_id == comp_id).order_by(models.ComponentVersion.version.desc())).scalars().first()
    if not v:
        return []
    return v.chat_history or []

def add_component_version(session: Session, comp_id, code: str, chat_history=None):
    last = session.execute(select(func.coalesce(func.max(models.ComponentVersion.version), 0)).where(models.ComponentVersion.component_id == comp_id)).scalar_one()
    new_version = int(last) + 1
    ver = models.ComponentVersion(id=uuid.uuid4(), component_id=comp_id, version=new_version, code=code, chat_history=chat_history)
    session.add(ver)
    session.commit()
    return get_component(session, comp_id)
