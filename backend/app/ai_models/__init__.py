# ──────────────────────────────────────────────────────────────
# VeriTruth AI — AI Models Package
# ──────────────────────────────────────────────────────────────
from app.ai_models.classifier import classify_fake_news, get_shap_explanations
from app.ai_models.claim_extractor import extract_claims, extract_entities
from app.ai_models.propaganda_detector import detect_propaganda
from app.ai_models.fact_verifier import verify_claims
from app.ai_models.sentiment_analyzer import analyze_sentiment
from app.ai_models.deepfake_detector import analyze_image, analyze_video_deepfake
from app.ai_models.credibility_scorer import compute_credibility_score
from app.ai_models.knowledge_graph import build_knowledge_graph

__all__ = [
    "classify_fake_news",
    "get_shap_explanations",
    "extract_claims",
    "extract_entities",
    "detect_propaganda",
    "verify_claims",
    "analyze_sentiment",
    "analyze_image",
    "analyze_video_deepfake",
    "compute_credibility_score",
    "build_knowledge_graph",
]
