from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from . import models, schemas, crud, db, transpiler_client

app = FastAPI(title="Bruno Component Manager")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

models.Base.metadata.create_all(bind=db.engine)

@app.post("/components/", response_model=schemas.ComponentOut)
def create_component(payload: schemas.ComponentCreate, session: Session = Depends(db.get_db)):
    # Ensure knowledge exists
    kb = crud.get_knowledge_by_name(session, payload.knowledge_name)
    if not kb:
        raise HTTPException(400, f"knowledge base '{payload.knowledge_name}' not found")
    # Call transpiler
    try:
        transpiler_resp = transpiler_client.transpile(payload.description, kb.spec)
    except Exception as e:
        raise HTTPException(502, f"Transpiler error: {e}")
    component = crud.create_component_with_version(session, payload.name, payload.description, kb.id, transpiler_resp["code"], transpiler_resp.get("chat_history"))
    return component

@app.post("/components/{component_id}/refine", response_model=schemas.ComponentOut)
def refine_component(component_id: str, payload: schemas.RefineRequest, session: Session = Depends(db.get_db)):
    comp = crud.get_component(session, component_id)
    if not comp:
        raise HTTPException(404, "component not found")
    # retrieve last chat history
    last_history = crud.get_latest_chat_history(session, comp.id)
    try:
        transpiler_resp = transpiler_client.transpile(payload.refinement, comp.knowledge_base.spec, context_chat_history=last_history)
    except Exception as e:
        raise HTTPException(502, f"Transpiler error: {e}")
    updated = crud.add_component_version(session, comp.id, transpiler_resp["code"], transpiler_resp.get("chat_history"))
    return updated

@app.get("/components/{component_id}", response_model=schemas.ComponentOut)
def get_component(component_id: str, session: Session = Depends(db.get_db)):
    comp = crud.get_component(session, component_id)
    if not comp:
        raise HTTPException(404, "component not found")
    return comp

@app.get("/components/{component_id}/history")
def get_history(component_id: str, session: Session = Depends(db.get_db)):
    history = crud.get_component_versions(session, component_id)
    if history is None:
        raise HTTPException(404, "component not found")
    return {"versions": history}
