from __future__ import annotations

from pathlib import Path

from app.services.audit import audit


def transcribe_audio(report_id: str, path: str) -> str:
    """Optional transcription.

    By default this is a stub. If you install `faster-whisper`, it will run locally.
    """
    try:
        from faster_whisper import WhisperModel

        model = WhisperModel("base", device="cpu", compute_type="int8")
        segments, info = model.transcribe(str(Path(path)), beam_size=1)
        text = " ".join(seg.text.strip() for seg in segments if seg.text)
        audit(report_id, "transcribe", {"language": getattr(info, "language", None), "chars": len(text)})
        return text
    except Exception as e:
        audit(report_id, "transcribe_failed", {"error": str(e)})
        return ""
