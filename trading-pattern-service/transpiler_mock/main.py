from fastapi import FastAPI, Request
from pydantic import BaseModel
app = FastAPI(title="Transpiler Mock")

class TranspileReq(BaseModel):
    request: str
    knowledge: dict = {}
    context: dict = {}

@app.post("/api/v1/transpiler/")
async def transpile(req: TranspileReq):
    # Produce deterministic fake python code that includes the request and a minimal function
    code = f"""def check_pattern(data):\n    \'\'\'Generated for request: {req.request}\n    Based on base pattern length: {len(str(req.knowledge.get('base_pattern','')))}\n    \'\'\'\n    # NOTE: This is mock code - replace with real transpiler output\n    return {{'matches': False}}\n"""
    chat_history = [{"role":"user","content": req.request}, {"role":"assistant","content": code}]
    return {"code": code, "chat_history": chat_history}
