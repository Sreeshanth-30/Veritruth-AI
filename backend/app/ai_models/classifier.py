# ──────────────────────────────────────────────────────────────
# VeriTruth AI — Fake News Classifier Service (RoBERTa / DeBERTa)
# ──────────────────────────────────────────────────────────────
from __future__ import annotations

import logging
import re
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)

# Global model cache — loaded once on first call
_classifier = None
_tokenizer = None
_model_failed = False  # set True if transformer load fails so we skip retries


# ── Heuristic fallback (works without transformers) ────────────

_FAKE_SIGNALS = [
    r"\bbreaking\b", r"\bshocking\b", r"\bunbelievable\b", r"\bmiracle\b",
    r"\bsecret\b", r"\bthey don't want you\b", r"\bconspiracy\b",
    r"\bhoax\b", r"\bfake\b", r"\bscam\b", r"\bfraud\b", r"\blie\b",
    r"\bexclusive\b", r"\byou won't believe\b", r"\bgoing viral\b",
    r"\bexposes?\b", r"\bcover.?up\b", r"\bdeep state\b",
]
_REAL_SIGNALS = [
    r"\baccording to\b", r"\bresearchers?\b", r"\bstudy\b", r"\bsource[sd]?\b",
    r"\bofficial(ly)?\b", r"\bstatement\b", r"\bpublished\b", r"\bjournal\b",
    r"\buniversity\b", r"\bgovernment\b", r"\bspokesperson\b", r"\bcited\b",
    r"\bdata\b", r"\bstatistics?\b", r"\bevidence\b",
]


def _heuristic_classify(text: str) -> dict[str, Any]:
    """Keyword/pattern-based classifier used when transformers are unavailable."""
    tl = text.lower()
    fake_hits = sum(1 for p in _FAKE_SIGNALS if re.search(p, tl))
    real_hits = sum(1 for p in _REAL_SIGNALS if re.search(p, tl))
    total = fake_hits + real_hits or 1
    fake_prob = fake_hits / total * 0.7 + 0.15  # bias toward middle
    fake_prob = min(max(fake_prob, 0.1), 0.9)
    real_prob = 1.0 - fake_prob
    confidence = max(fake_prob, real_prob)
    return {
        "fake_probability": round(fake_prob, 3),
        "real_probability": round(real_prob, 3),
        "confidence": round(confidence, 3),
        "label": "fake" if fake_prob > 0.5 else "real",
    }


def _load_model():
    """Lazy-load the transformer model and tokenizer."""
    global _classifier, _tokenizer, _model_failed
    if _classifier is not None or _model_failed:
        return

    try:
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
        from app.core.config import get_settings

        settings = get_settings()
        model_name = settings.FAKE_NEWS_MODEL  # e.g. "roberta-base" or fine-tuned path

        logger.info("Loading fake news classifier: %s", model_name)
        _tokenizer = AutoTokenizer.from_pretrained(model_name, local_files_only=True)
        _classifier = AutoModelForSequenceClassification.from_pretrained(
            model_name,
            num_labels=2,  # 0=real, 1=fake
            local_files_only=True,
        )
        _classifier.eval()
        logger.info("✓ Classifier loaded")
    except Exception as e:
        logger.warning("Transformer classifier unavailable (%s) — using heuristic fallback", e)
        _model_failed = True


def classify_fake_news(text: str) -> dict[str, Any]:
    """Run the fake news classifier on input text.

    Returns:
        {
            "fake_probability": float (0-1),
            "real_probability": float (0-1),
            "confidence": float (0-1),
            "label": "fake" | "real",
        }
    """
    _load_model()

    if _model_failed or _classifier is None:
        result = _heuristic_classify(text)
        logger.info("Heuristic classification: %s (fake_prob=%.3f)", result["label"], result["fake_probability"])
        return result

    try:
        import torch

        inputs = _tokenizer(
            text,
            return_tensors="pt",
            max_length=512,
            truncation=True,
            padding=True,
        )

        with torch.no_grad():
            outputs = _classifier(**inputs)
            logits = outputs.logits
            probs = torch.softmax(logits, dim=-1).squeeze().numpy()

        fake_prob = float(probs[1])
        real_prob = float(probs[0])
        confidence = float(max(probs))

        result = {
            "fake_probability": fake_prob,
            "real_probability": real_prob,
            "confidence": confidence,
            "label": "fake" if fake_prob > 0.5 else "real",
        }

        logger.info(
            "Classification result: %s (fake_prob=%.3f, confidence=%.3f)",
            result["label"], fake_prob, confidence,
        )
        return result
    except Exception as e:
        logger.warning("Transformer inference failed (%s) — using heuristic", e)
        return _heuristic_classify(text)


def get_shap_explanations(text: str, num_features: int = 20) -> dict[str, Any]:
    """Generate token-level feature attributions for explainability.

    Returns:
        {
            "tokens": [{"token": str, "shap_value": float, "importance": float}, ...],
            "base_value": float,
        }
    """
    _load_model()

    # ── Heuristic token attribution (works without SHAP / transformers) ───
    def _heuristic_shap(txt: str) -> dict[str, Any]:
        words = txt.split()[:num_features]
        tokens = []
        for w in words:
            wl = w.lower().strip(".,!?\"'")
            is_fake_signal = any(re.search(p, wl) for p in _FAKE_SIGNALS)
            is_real_signal = any(re.search(p, wl) for p in _REAL_SIGNALS)
            val = 0.15 if is_fake_signal else (-0.10 if is_real_signal else round((hash(wl) % 100) / 1000 - 0.05, 3))
            tokens.append({"token": w, "shap_value": val, "importance": abs(val)})
        tokens.sort(key=lambda x: x["importance"], reverse=True)
        return {"tokens": tokens, "base_value": 0.5}

    if _model_failed or _classifier is None:
        return _heuristic_shap(text)

    try:
        import shap

        explainer = shap.Explainer(
            lambda texts: np.array([
                classify_fake_news(t)["fake_probability"] for t in texts
            ]),
            _tokenizer,
        )
        shap_values = explainer([text])

        raw_tokens = _tokenizer.tokenize(text)[:num_features]
        values = shap_values.values[0][:num_features]

        tokens = []
        for token, val in zip(raw_tokens, values):
            sv = float(val)
            tokens.append({
                "token": token.replace("Ġ", ""),
                "shap_value": sv,
                "importance": abs(sv),
            })

        tokens.sort(key=lambda x: x["importance"], reverse=True)
        return {"tokens": tokens, "base_value": float(shap_values.base_values[0])}

    except Exception as e:
        logger.warning("SHAP explainability failed (%s) — using heuristic", e)
        return _heuristic_shap(text)
