from app.config import settings

def evaluate_risk(regex_count: int, guard_triggered: bool, doc_injection_triggered: bool, pii_found: bool) -> tuple[int, str, bool]:
    score = 0
    
    if regex_count > 0:
        score += settings.weight_regex_match * min(regex_count, 2)
    if guard_triggered:
        score += settings.weight_llama_guard_unsafe
    if doc_injection_triggered:
        score += settings.weight_document_injection
    if pii_found:
        score += settings.weight_pii_present

    # Clamp upper boundary
    score = min(score, 100)
    
    # Determine risk thresholds
    blocked = score >= settings.block_threshold
    if blocked:
        level = "BLOCKED"
    elif score > settings.threshold_high_max:
        level = "HIGH"
    elif score > settings.threshold_medium_max:
        level = "MEDIUM"
    else:
        level = "LOW"
        
    return score, level, blocked