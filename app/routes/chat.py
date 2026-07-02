from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import json

from app.models.schemas import ChatRequest, DocumentChatRequest, ChatResponse
from app.db.database import get_db
from app.db.models import AuditLog
from app.llm.client import generate, LLMClientError
from app.config import settings

from app.detection.regex_filter import scan_prompt_regex
from app.detection.llama_guard import check_prompt_safety
from app.detection.pii_detector import scan_and_redact_pii
from app.scoring.risk_engine import evaluate_risk

router = APIRouter(prefix="/v1", tags=["chat"])

@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, db: Session = Depends(get_db)):
    reasons = []
    regex_hits = scan_prompt_regex(req.prompt) if settings.enable_regex_filter else []
    if regex_hits:
        reasons.extend(regex_hits)
        
    lg_unsafe, lg_reason = await check_prompt_safety(req.prompt) if settings.enable_llama_guard else (False, "")
    if lg_unsafe:
        reasons.append(lg_reason)
        
    score, level, blocked = evaluate_risk(len(regex_hits), lg_unsafe, False, False)
    
    if blocked:
        log_entry = AuditLog(user_id=req.user_id, endpoint="/v1/chat", prompt=req.prompt, response="", risk_score=score, risk_level=level, blocked=True, detection_reasons=reasons)
        db.add(log_entry); db.commit()
        return ChatResponse(response="Request blocked due to security policies.", risk_score=score, risk_level=level, blocked=True, reasons=reasons)

    try:
        raw_response = await generate(req.prompt)
    except LLMClientError as e:
        raise HTTPException(status_code=502, detail=str(e))
        
    # Post-flight output scanning (PII check)
    final_response, pii_labels = scan_and_redact_pii(raw_response) if settings.enable_pii_detection else (raw_response, [])
    if pii_labels:
        reasons.extend([f"output_pii_{label.lower()}" for label in pii_labels])
        score, level, blocked = evaluate_risk(len(regex_hits), lg_unsafe, False, True)

    log_entry = AuditLog(user_id=req.user_id, endpoint="/v1/chat", prompt=req.prompt, response=final_response, risk_score=score, risk_level=level, blocked=False, detection_reasons=reasons)
    db.add(log_entry); db.commit()
    
    return ChatResponse(response=final_response, risk_score=score, risk_level=level, blocked=False, reasons=reasons)

@router.post("/chat-with-document", response_model=ChatResponse)
async def chat_with_document(req: DocumentChatRequest, db: Session = Depends(get_db)):
    reasons = []
    
    # Indirect Injection Check: Scan Document Contents using baseline heuristics
    doc_regex_hits = scan_prompt_regex(req.document_content) if settings.enable_regex_filter else []
    if doc_regex_hits:
        reasons.extend([f"indirect_{hit}" for hit in doc_regex_hits])
        
    user_prompt_hits = scan_prompt_regex(req.prompt) if settings.enable_regex_filter else []
    reasons.extend(user_prompt_hits)
    
    lg_unsafe, lg_reason = await check_prompt_safety(req.prompt + " " + req.document_content) if settings.enable_llama_guard else (False, "")
    if lg_unsafe:
        reasons.append(f"combined_{lg_reason}")
        
    score, level, blocked = evaluate_risk(len(user_prompt_hits), lg_unsafe, len(doc_regex_hits) > 0, False)
    
    if blocked:
        log_entry = AuditLog(user_id=req.user_id, endpoint="/v1/chat-with-document", prompt=f"Prompt: {req.prompt} | Doc: {req.document_content[:200]}...", response="", risk_score=score, risk_level=level, blocked=True, detection_reasons=reasons)
        db.add(log_entry); db.commit()
        return ChatResponse(response="Request blocked due to indirect security profile risks.", risk_score=score, risk_level=level, blocked=True, reasons=reasons)

    combined_context = f"Document Context:\n{req.document_content}\n\nUser Question: {req.prompt}"
    try:
        raw_response = await generate(combined_context)
    except LLMClientError as e:
        raise HTTPException(status_code=502, detail=str(e))
        
    final_response, pii_labels = scan_and_redact_pii(raw_response) if settings.enable_pii_detection else (raw_response, [])
    
    log_entry = AuditLog(user_id=req.user_id, endpoint="/v1/chat-with-document", prompt=req.prompt, response=final_response, risk_score=score, risk_level=level, blocked=False, detection_reasons=reasons)
    db.add(log_entry); db.commit()
    
    return ChatResponse(response=final_response, risk_score=score, risk_level=level, blocked=False, reasons=reasons)