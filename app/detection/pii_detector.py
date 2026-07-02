import re

PII_PATTERNS = {
    "EMAIL": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    "PHONE": r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
    "CREDIT_CARD": r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b",
    "SSN": r"\b\d{3}-\d{2}-\d{4}\b"
}

def scan_and_redact_pii(text: str) -> tuple[str, list[str]]:
    """Scans text for PII patterns, returns redacted text and found labels."""
    redacted_text = text
    found_labels = []
    
    for label, pattern in PII_PATTERNS.items():
        matches = re.findall(pattern, redacted_text)
        if matches:
            found_labels.append(label)
            redacted_text = re.sub(pattern, f"[{label}_REDACTED]", redacted_text)
            
    return redacted_text, found_labels