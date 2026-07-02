from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import AuditLog
from sqlalchemy import func

router = APIRouter(prefix="/v1/admin", tags=["admin"])

@router.get("/logs")
def get_logs(limit: int = 50, db: Session = Depends(get_db)):
    logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit).all()
    return logs

@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    total = db.query(AuditLog).count()
    blocked = db.query(AuditLog).filter(AuditLog.blocked == True).count()
    
    by_level = db.query(AuditLog.risk_level, func.count(AuditLog.id)).group_by(AuditLog.risk_level).all()
    level_distribution = {level: count for level, count in by_level}
    
    return {
        "total_requests": total,
        "blocked_count": blocked,
        "by_risk_level": level_distribution
    }