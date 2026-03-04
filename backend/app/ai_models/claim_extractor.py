# ──────────────────────────────────────────────────────────────
# VeriTruth AI — Claim Extraction Service (spaCy NLP)
# ──────────────────────────────────────────────────────────────
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

_nlp = None
_spacy_failed = False


def _heuristic_extract_claims(text: str) -> list[dict[str, Any]]:
    """Regex-based claim extraction — fallback when spaCy is unavailable."""
    import re
    sentences = [s.strip() for s in re.split(r"[.!?]", text) if len(s.strip()) > 20]
    claims = []
    for i, sent in enumerate(sentences[:30]):
        has_numbers = bool(re.search(r"\d", sent))
        is_quote = '"' in sent or "\u2018" in sent or "\u2019" in sent or "\u201c" in sent
        # Simple entity-like detection: consecutive capitalised words
        entities = re.findall(r"(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)", sent)
        score = 0.2
        if has_numbers:
            score += 0.3
        if is_quote:
            score += 0.2
        if entities:
            score += 0.2
        if score >= 0.3:
            claims.append({
                "claim_text": sent,
                "entities": [{"text": e, "label": "ENTITY"} for e in entities[:3]],
                "has_numbers": has_numbers,
                "is_quote": is_quote,
                "sentence_index": i,
                "confidence": round(score, 2),
            })
    return claims[:15]


def _heuristic_extract_entities(text: str) -> list[dict[str, Any]]:
    """Simple regex entity extractor when spaCy is unavailable."""
    import re
    entities = []
    for match in re.findall(r"(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})", text):
        entities.append({"text": match, "label": "ENTITY"})
    return entities[:20]


def _load_spacy():
    global _nlp, _spacy_failed
    if _nlp is not None or _spacy_failed:
        return

    try:
        import spacy
        from app.core.config import get_settings

        model = get_settings().SPACY_MODEL
        try:
            _nlp = spacy.load(model)
        except OSError:
            logger.warning("spaCy model %s not found, falling back to en_core_web_sm", model)
            try:
                _nlp = spacy.load("en_core_web_sm")
            except OSError:
                import subprocess
                result = subprocess.run(
                    ["python", "-m", "spacy", "download", "en_core_web_sm"],
                    capture_output=True,
                )
                if result.returncode == 0:
                    _nlp = spacy.load("en_core_web_sm")
                else:
                    raise RuntimeError("spaCy download failed")
        logger.info("✓ spaCy model loaded")
    except Exception as e:
        logger.warning("spaCy unavailable (%s) — using regex-based claim extraction", e)
        _spacy_failed = True


def extract_claims(text: str) -> list[dict[str, Any]]:
    """Extract verifiable claims from article text using spaCy NLP."""
    _load_spacy()

    if _spacy_failed or _nlp is None:
        return _heuristic_extract_claims(text)

    try:
        doc = _nlp(text)
        claims = []

        claim_verbs = {
            "claim", "report", "state", "announce", "reveal",
            "discover", "find", "show", "prove", "demonstrate",
            "confirm", "deny", "suggest", "indicate", "cause",
        }

        for i, sent in enumerate(doc.sents):
            sent_text = sent.text.strip()
            if len(sent_text) < 20:
                continue

            entities = [{"text": ent.text, "label": ent.label_} for ent in sent.ents]
            has_numbers = any(tok.like_num or tok.ent_type_ in ("CARDINAL", "PERCENT", "MONEY") for tok in sent)
            has_claim_verb = any(tok.lemma_.lower() in claim_verbs for tok in sent)
            is_quote = '"' in sent_text or "'" in sent_text
            has_named_entities = len(entities) > 0

            score = 0.0
            if has_numbers:
                score += 0.3
            if has_claim_verb:
                score += 0.25
            if is_quote:
                score += 0.15
            if has_named_entities:
                score += 0.2
            if any(tok.dep_ in ("nsubj", "nsubjpass") and tok.ent_type_ for tok in sent):
                score += 0.1

            if score >= 0.3 or (has_named_entities and has_numbers):
                claims.append({
                    "claim_text": sent_text,
                    "entities": entities,
                    "has_numbers": has_numbers,
                    "is_quote": is_quote,
                    "sentence_index": i,
                    "start_char": sent.start_char,
                    "end_char": sent.end_char,
                    "confidence": min(score, 1.0),
                })

        logger.info("Extracted %d claims from %d sentences", len(claims), len(list(doc.sents)))
        return claims
    except Exception as e:
        logger.warning("spaCy claim extraction failed (%s) — regex fallback", e)
        return _heuristic_extract_claims(text)


def extract_entities(text: str) -> list[dict[str, str]]:
    """Extract named entities for knowledge graph construction."""
    _load_spacy()

    if _spacy_failed or _nlp is None:
        return _heuristic_extract_entities(text)

    try:
        doc = _nlp(text)
        entities = []
        seen: set[tuple[str, str]] = set()
        for ent in doc.ents:
            key = (ent.text.lower(), ent.label_)
            if key not in seen:
                seen.add(key)
                entities.append({
                    "text": ent.text,
                    "label": ent.label_,
                    "start": ent.start_char,
                    "end": ent.end_char,
                })
        return entities
    except Exception as e:
        logger.warning("spaCy entity extraction failed (%s) — regex fallback", e)
        return _heuristic_extract_entities(text)

