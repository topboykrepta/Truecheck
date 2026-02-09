from __future__ import annotations

from pathlib import Path

from app.services.audit import audit


def ocr_image(report_id: str, path: str) -> str:
    """Optional OCR.

    Requires `pytesseract` and a local Tesseract install.
    If unavailable, returns empty string and records a limitation.
    """
    try:
        from PIL import Image
        import pytesseract

        img = Image.open(Path(path))
        text = pytesseract.image_to_string(img)
        audit(report_id, "ocr", {"chars": len(text or "")})
        return text or ""
    except Exception as e:
        audit(report_id, "ocr_failed", {"error": str(e)})
        return ""
