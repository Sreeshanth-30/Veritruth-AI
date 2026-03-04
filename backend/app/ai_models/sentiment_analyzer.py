# ──────────────────────────────────────────────────────────────
# VeriTruth AI — Sentiment & Emotion Classifier
# ──────────────────────────────────────────────────────────────
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

_model = None
_tokenizer = None
_model_failed = False


def _heuristic_sentiment(text: str) -> dict:
    """Rule-based sentiment analysis — works without any ML library."""
    tl = text.lower()
    pos_words = ["good", "great", "excellent", "positive", "success", "win", "benefit", "improve", "hope", "support", "true", "confirm"]
    neg_words = ["bad", "terrible", "awful", "negative", "fail", "threat", "dangerous", "corrupt", "lie", "attack", "crisis", "wrong", "false"]
    manip_words = ["must", "urgent", "act now", "emergency", "warning", "shocking", "secret", "expose", "destroy", "evil", "conspiracy"]

    pos_score = sum(1 for w in pos_words if w in tl)
    neg_score = sum(1 for w in neg_words if w in tl)
    manip_score = sum(1 for w in manip_words if w in tl)

    total = pos_score + neg_score or 1
    sentiment_ratio = (pos_score - neg_score) / total
    if sentiment_ratio > 0.2:
        overall = "positive"
        score = min(sentiment_ratio, 1.0)
    elif sentiment_ratio < -0.2:
        overall = "negative"
        score = max(sentiment_ratio, -1.0)
    else:
        overall = "neutral"
        score = sentiment_ratio

    manip_pct = min(manip_score / max(len(text.split()) / 10, 1) * 100, 100)
    indicators = []
    if manip_pct > 30:
        indicators.append("High use of urgency/fear language")
    if neg_score > pos_score * 2:
        indicators.append("Predominantly negative framing")
    if "!" in text:
        indicators.append("Excessive exclamation marks")
    return {
        "overall_sentiment": overall,
        "sentiment_score": round(score, 3),
        "emotions": {
            "fear": round(min(neg_score * 8.0, 100), 1),
            "excitement": round(min(pos_score * 7.0, 100), 1),
            "anger": round(min(neg_score * 6.0, 100), 1),
            "trust": round(min(pos_score * 9.0, 100), 1),
            "surprise": round(min(manip_score * 5.0, 100), 1),
            "disgust": round(min(neg_score * 5.0, 100), 1),
        },
        "emotional_manipulation_score": round(manip_pct, 1),
        "manipulation_score": round(manip_pct / 100, 3),
        "manipulation_indicators": indicators,
    }


def _load_model():
    global _model, _tokenizer, _model_failed
    if _model is not None or _model_failed:
        return

    try:
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
        from app.core.config import get_settings

        model_name = get_settings().SENTIMENT_MODEL
        logger.info("Loading sentiment model: %s", model_name)
        _tokenizer = AutoTokenizer.from_pretrained(model_name, local_files_only=True)
        _model = AutoModelForSequenceClassification.from_pretrained(model_name, local_files_only=True)
        _model.eval()
        logger.info("✓ Sentiment model loaded")
    except Exception as e:
        logger.warning("Sentiment model unavailable (%s) — using heuristic fallback", e)
        _model_failed = True


def analyze_sentiment(text: str) -> dict[str, Any]:
    """Perform multi-dimensional sentiment and emotion analysis."""
    _load_model()

    if _model_failed or _model is None:
        return _heuristic_sentiment(text)

    try:
        import torch
        import numpy as np

        # Split text into chunks for long articles
        chunks = [text[i:i+512] for i in range(0, len(text), 450)]
        all_sentiments = []

        for chunk in chunks[:10]:  # Max 10 chunks
            inputs = _tokenizer(
                chunk,
                return_tensors="pt",
                max_length=512,
                truncation=True,
                padding=True,
            )

            with torch.no_grad():
                outputs = _model(**inputs)
                probs = torch.softmax(outputs.logits, dim=-1).squeeze().numpy()

            all_sentiments.append(probs)

        avg_probs = np.mean(all_sentiments, axis=0)

        # Map to emotions (extended analysis)
        emotions = _compute_emotions(text, avg_probs)
        manipulation_score, indicators = _detect_manipulation(text, emotions)

        labels = ["negative", "neutral", "positive"]
        overall_idx = int(np.argmax(avg_probs))

        return {
            "overall_sentiment": labels[min(overall_idx, len(labels) - 1)],
            "sentiment_score": float(avg_probs[-1] - avg_probs[0]),
            "emotions": emotions,
            "emotional_manipulation_score": manipulation_score,
            "manipulation_score": manipulation_score / 100,
            "manipulation_indicators": indicators,
        }
    except Exception as e:
        logger.warning("Sentiment transformer failed (%s) — heuristic fallback", e)
        return _heuristic_sentiment(text)


def _compute_emotions(text: str, sentiment_probs) -> dict[str, float]:
    """Compute granular emotion scores from text features and sentiment."""
    text_lower = text.lower()

    # Keyword-based emotion indicators
    fear_words = {"fear", "terrifying", "alarming", "dangerous", "threat", "deadly", "catastroph", "panic", "crisis"}
    anger_words = {"outrage", "furious", "disgraceful", "corrupt", "scandal", "betrayal", "abuse", "exploit"}
    excitement_words = {"breakthrough", "amazing", "incredible", "revolutionary", "miracle", "stunning", "extraordinary"}
    surprise_words = {"shocking", "unexpected", "unbelievable", "breaking", "revealed", "secret", "hidden"}
    disgust_words = {"disgusting", "appalling", "sickening", "vile", "repulsive", "shameful"}
    trust_words = {"confirmed", "verified", "according to", "study shows", "research indicates", "evidence"}

    word_count = max(len(text.split()), 1)

    def score(keywords):
        count = sum(1 for w in keywords if w in text_lower)
        return min(count / (word_count / 100) * 25, 100)

    emotions = {
        "fear": round(score(fear_words) + float(sentiment_probs[0]) * 30, 1),
        "excitement": round(score(excitement_words) + float(sentiment_probs[-1]) * 20, 1),
        "anger": round(score(anger_words) + float(sentiment_probs[0]) * 20, 1),
        "trust": round(score(trust_words) + float(sentiment_probs[-1]) * 25, 1),
        "surprise": round(score(surprise_words) + 15, 1),
        "disgust": round(score(disgust_words) + float(sentiment_probs[0]) * 15, 1),
    }

    # Cap at 100
    return {k: min(v, 100) for k, v in emotions.items()}


def _detect_manipulation(
    text: str, emotions: dict[str, float]
) -> tuple[float, list[str]]:
    """Detect emotional manipulation patterns.

    Signs of manipulation:
    - Extreme emotional language
    - Fear + urgency combination
    - Outrage amplification
    - Appeal to emotion over facts
    """
    indicators = []
    score = 0.0

    text_lower = text.lower()

    # High fear + urgency
    if emotions["fear"] > 60:
        urgency = sum(1 for w in ["urgent", "immediately", "now", "before it's too late", "act fast"] if w in text_lower)
        if urgency > 0:
            indicators.append("Fear-urgency combination detected")
            score += 25

    # Outrage amplification
    if emotions["anger"] > 50:
        caps_ratio = sum(1 for c in text if c.isupper()) / max(len(text), 1)
        if caps_ratio > 0.1:
            indicators.append("Outrage amplification with emphasis")
            score += 20

    # Emotional over factual
    emotional_total = emotions["fear"] + emotions["anger"] + emotions["excitement"]
    if emotional_total > 180 and emotions["trust"] < 30:
        indicators.append("High emotional content with low factual trust signals")
        score += 30

    # Exclamation overuse
    excl_count = text.count("!")
    if excl_count > 3:
        indicators.append(f"Excessive exclamation usage ({excl_count} instances)")
        score += min(excl_count * 5, 25)

    return min(score, 100), indicators
