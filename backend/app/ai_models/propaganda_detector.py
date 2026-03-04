# ──────────────────────────────────────────────────────────────
# VeriTruth AI — Propaganda Detection Engine (fine-tuned BERT)
# ──────────────────────────────────────────────────────────────
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

_model = None
_tokenizer = None
_model_failed = False

# 18 propaganda techniques per SemEval-2020 Task 11
PROPAGANDA_TECHNIQUES = [
    "Loaded Language",
    "Name Calling / Labeling",
    "Repetition",
    "Exaggeration / Minimisation",
    "Appeal to Fear / Prejudice",
    "Flag-Waving",
    "Causal Oversimplification",
    "Appeal to Authority",
    "Black-and-White Fallacy",
    "Bandwagon / Reductio ad Hitlerum",
    "Doubt",
    "Slogans",
    "Thought-Terminating Cliché",
    "Whataboutism / Straw Man / Red Herring",
    "Obfuscation / Intentional Vagueness",
    "Presenting Irrelevant Data",
    "Smears",
    "Appeal to Emotion",
]

# Keyword sets for heuristic fallback
_TECHNIQUE_KEYWORDS: dict[str, list[str]] = {
    "Loaded Language": ["horrifying", "disgusting", "outrageous", "evil", "radical", "extreme", "awful", "terrible"],
    "Appeal to Fear / Prejudice": ["threat", "dangerous", "attack", "invasion", "crisis", "catastrophe", "destroy"],
    "Exaggeration / Minimisation": ["never", "always", "everyone", "nobody", "completely", "absolutely", "worst ever"],
    "Name Calling / Labeling": ["idiot", "criminal", "terrorist", "liar", "corrupt", "traitor", "extremist"],
    "Appeal to Authority": ["experts say", "scientists agree", "officials claim", "studies show"],
    "Causal Oversimplification": ["because of", "caused by", "responsible for", "to blame"],
    "Slogans": ["make america", "together we", "yes we can", "the truth is out"],
    "Appeal to Emotion": ["heartbreaking", "devastating", "wonderful", "amazing", "unbelievable"],
}


def _heuristic_propaganda(text: str) -> dict[str, Any]:
    tl = text.lower()
    techniques_found: dict[str, Any] = {}
    for technique, keywords in _TECHNIQUE_KEYWORDS.items():
        hits = [kw for kw in keywords if kw in tl]
        if hits:
            instances = [s.strip() for s in text.replace("!", ".").replace("?", ".").split(".") if any(h in s.lower() for h in hits)][:2]
            techniques_found[technique] = {
                "technique": technique,
                "confidence": min(0.35 + len(hits) * 0.1, 0.85),
                "instances": instances,
            }
    overall = sum(t["confidence"] for t in techniques_found.values()) / len(PROPAGANDA_TECHNIQUES) * 100 if techniques_found else 0.0
    return {
        "overall_score": round(min(overall, 100), 1),
        "techniques": sorted(techniques_found.values(), key=lambda x: x["confidence"], reverse=True),
        "heatmap_data": [],
    }


def _load_model():
    global _model, _tokenizer, _model_failed
    if _model is not None or _model_failed:
        return

    try:
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
        from app.core.config import get_settings

        model_name = get_settings().PROPAGANDA_MODEL
        logger.info("Loading propaganda detector: %s", model_name)

        _tokenizer = AutoTokenizer.from_pretrained(model_name, local_files_only=True)
        _model = AutoModelForSequenceClassification.from_pretrained(
            model_name,
            num_labels=len(PROPAGANDA_TECHNIQUES),
            problem_type="multi_label_classification",
            local_files_only=True,
        )
        _model.eval()
        logger.info("✓ Propaganda detector loaded")
    except Exception as e:
        logger.warning("Propaganda detector unavailable (%s) — using heuristic fallback", e)
        _model_failed = True


def detect_propaganda(text: str) -> dict[str, Any]:
    """Detect propaganda techniques in text using a multi-label classifier.

    Falls back to keyword heuristics when transformers are unavailable.
    """
    _load_model()

    if _model_failed or _model is None:
        return _heuristic_propaganda(text)

    try:
        import torch

        sentences = [
            s.strip()
            for s in text.replace("!", ".").replace("?", ".").split(".")
            if len(s.strip()) > 15
        ]

        all_techniques: dict[str, Any] = {}
        heatmap_data = []

        for sent in sentences:
            inputs = _tokenizer(
                sent,
                return_tensors="pt",
                max_length=256,
                truncation=True,
                padding=True,
            )

            with torch.no_grad():
                outputs = _model(**inputs)
                probs = torch.sigmoid(outputs.logits).squeeze().numpy()

            sent_score = 0.0
            for technique, prob in zip(PROPAGANDA_TECHNIQUES, probs):
                prob_val = float(prob)
                if prob_val > 0.3:
                    if technique not in all_techniques:
                        all_techniques[technique] = {
                            "technique": technique,
                            "confidence": prob_val,
                            "instances": [],
                        }
                    else:
                        all_techniques[technique]["confidence"] = max(
                            all_techniques[technique]["confidence"], prob_val
                        )
                    all_techniques[technique]["instances"].append(sent)
                    sent_score = max(sent_score, prob_val)

            heatmap_data.append({"text": sent, "intensity": sent_score})

        if all_techniques:
            overall = (
                sum(t["confidence"] for t in all_techniques.values())
                / len(PROPAGANDA_TECHNIQUES)
                * 100
            )
        else:
            overall = 0.0

        result = {
            "overall_score": min(overall, 100),
            "techniques": sorted(
                all_techniques.values(),
                key=lambda x: x["confidence"],
                reverse=True,
            ),
            "heatmap_data": heatmap_data,
        }

        logger.info(
            "Propaganda detection: score=%.1f, techniques=%d",
            result["overall_score"],
            len(result["techniques"]),
        )
        return result

    except Exception as e:
        logger.warning("Propaganda transformer inference failed (%s) — heuristic fallback", e)
        return _heuristic_propaganda(text)
