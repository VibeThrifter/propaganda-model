#!/usr/bin/env python3
"""Een podcast-aflevering lokaal omzetten in tekst (faster-whisper, CPU). Draait onder
tools/kanalen/.venv; wordt aangeroepen door ophalen.py voor platform `podcast`.

    tools/kanalen/.venv/bin/python tools/kanalen/transcribeer.py <audio-url> [--taal nl]

Schrijft de tekst naar stdout, met een tijdmarkering [mm:ss] per ~30 s, zoals de YouTube-
transcripts. Model: env KANALEN_WHISPER_MODEL (standaard "small"; "medium" is nauwkeuriger
maar ~3× trager). Gratis en lokaal; niets verlaat de machine behalve het downloaden van de audio.
"""
import argparse
import os
import sys
import tempfile
import urllib.request
from pathlib import Path

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) kanalen-monitor"


def tijd(s: float) -> str:
    u, r = divmod(int(s), 3600)
    return f"{u}:{r // 60:02d}:{r % 60:02d}" if u else f"{r // 60:02d}:{r % 60:02d}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("--taal", default="nl")
    a = ap.parse_args()
    import av
    _open = av.open

    def _open_zonder_metadata_errors(*args, **kw):   # PyAV ≥ 15 kent dit argument niet meer
        kw.pop("metadata_errors", None)
        return _open(*args, **kw)
    av.open = _open_zonder_metadata_errors
    from faster_whisper import WhisperModel
    with tempfile.TemporaryDirectory() as tmp:
        pad = Path(tmp) / "audio"
        req = urllib.request.Request(a.url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=120) as r, open(pad, "wb") as f:
            while blok := r.read(1 << 20):
                f.write(blok)
        model = WhisperModel(os.environ.get("KANALEN_WHISPER_MODEL", "small"),
                             device="cpu", compute_type="int8")
        segmenten, _ = model.transcribe(str(pad), language=a.taal, vad_filter=True)
        laatste = -999.0
        for seg in segmenten:
            if seg.start - laatste >= 30:
                sys.stdout.write(f"\n[{tijd(seg.start)}] ")
                laatste = seg.start
            sys.stdout.write(seg.text.strip() + " ")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
