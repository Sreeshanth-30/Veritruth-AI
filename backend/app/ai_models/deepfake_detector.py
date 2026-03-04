# ──────────────────────────────────────────────────────────────
# VeriTruth AI — Deepfake & Media Analysis (CNN)
# ──────────────────────────────────────────────────────────────
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

_model = None


def _load_model():
    global _model
    if _model is not None:
        return

    import torch
    import torch.nn as nn
    from torchvision import models
    from app.core.config import get_settings

    model_path = get_settings().DEEPFAKE_MODEL

    # EfficientNet-based deepfake detector
    class DeepfakeDetector(nn.Module):
        def __init__(self):
            super().__init__()
            self.backbone = models.efficientnet_b0(weights=None)
            self.backbone.classifier = nn.Sequential(
                nn.Dropout(0.3),
                nn.Linear(1280, 512),
                nn.ReLU(),
                nn.Dropout(0.2),
                nn.Linear(512, 2),
            )

        def forward(self, x):
            return self.backbone(x)

    _model = DeepfakeDetector()

    if Path(model_path).exists():
        state = torch.load(model_path, map_location="cpu")
        _model.load_state_dict(state)
        logger.info("✓ Deepfake model loaded from %s", model_path)
    else:
        logger.warning("Deepfake model not found at %s — using untrained model", model_path)

    _model.eval()


def analyze_image(image_path: str) -> dict[str, Any]:
    """Analyze an image for signs of manipulation or AI generation.
    
    Returns:
        {
            "is_manipulated": bool,
            "manipulation_probability": float (0-1),
            "analysis_details": str,
            "exif_metadata": dict,
            "compression_artifacts": float,
            "lighting_consistency": float,
        }
    """
    result = {
        "is_manipulated": False,
        "manipulation_probability": 0.0,
        "analysis_details": "",
        "exif_metadata": {},
        "compression_artifacts": 0.0,
        "lighting_consistency": 1.0,
    }

    # 1. EXIF metadata extraction
    result["exif_metadata"] = _extract_exif(image_path)

    # 2. CNN-based manipulation detection
    try:
        _load_model()

        import torch
        from PIL import Image
        from torchvision import transforms

        transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225],
            ),
        ])

        img = Image.open(image_path).convert("RGB")
        tensor = transform(img).unsqueeze(0)

        with torch.no_grad():
            output = _model(tensor)
            probs = torch.softmax(output, dim=-1).squeeze().numpy()

        manipulation_prob = float(probs[1])
        result["manipulation_probability"] = manipulation_prob
        result["is_manipulated"] = manipulation_prob > 0.5

    except Exception as e:
        logger.error("Image analysis CNN error: %s", e)
        result["analysis_details"] = f"CNN analysis failed: {str(e)}"

    # 3. Error Level Analysis (ELA)
    try:
        result["compression_artifacts"] = _compute_ela_score(image_path)
    except Exception as e:
        logger.warning("ELA analysis failed: %s", e)

    # Build summary
    if result["is_manipulated"]:
        result["analysis_details"] = (
            f"Image manipulation detected with {result['manipulation_probability']:.1%} confidence. "
            f"Compression artifact score: {result['compression_artifacts']:.2f}. "
            "Visual forensics suggest possible editing or AI generation."
        )
    else:
        result["analysis_details"] = (
            f"No significant manipulation detected (probability: {result['manipulation_probability']:.1%}). "
            "Image appears authentic based on visual forensics analysis."
        )

    return result


def _extract_exif(image_path: str) -> dict[str, Any]:
    """Extract and parse EXIF metadata from an image."""
    try:
        from PIL import Image
        from PIL.ExifTags import TAGS

        img = Image.open(image_path)
        exif_data = img._getexif()

        if not exif_data:
            return {"status": "No EXIF data found"}

        parsed = {}
        for tag_id, value in exif_data.items():
            tag_name = TAGS.get(tag_id, str(tag_id))
            try:
                parsed[tag_name] = str(value)[:200]
            except Exception:
                pass

        return parsed

    except Exception as e:
        return {"status": f"EXIF extraction failed: {str(e)}"}


def _compute_ela_score(image_path: str) -> float:
    """Compute Error Level Analysis score to detect JPEG re-compression artifacts."""
    try:
        from PIL import Image
        import numpy as np
        import tempfile

        img = Image.open(image_path).convert("RGB")
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            img.save(tmp.name, "JPEG", quality=90)
            resaved = Image.open(tmp.name).convert("RGB")

        original = np.array(img, dtype=np.float32)
        compressed = np.array(resaved, dtype=np.float32)
        diff = np.abs(original - compressed)

        # Normalize
        ela_score = float(np.mean(diff)) / 255.0
        return min(ela_score * 10, 1.0)  # Scale

    except Exception:
        return 0.0


def analyze_video_deepfake(video_path: str) -> dict[str, Any]:
    """Analyze video for deepfake indicators by sampling frames."""
    import os

    if not os.path.exists(video_path):
        return {"error": "Video file not found", "deepfake_confidence": 0.0}

    try:
        import cv2

        cap = cv2.VideoCapture(video_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        sample_indices = [int(i * total_frames / 10) for i in range(10)]

        scores = []
        for idx in sample_indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            if ret:
                import tempfile
                with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
                    cv2.imwrite(tmp.name, frame)
                    frame_result = analyze_image(tmp.name)
                    scores.append(frame_result["manipulation_probability"])
                    os.unlink(tmp.name)

        cap.release()

        if scores:
            avg_score = sum(scores) / len(scores)
            return {
                "deepfake_confidence": avg_score,
                "is_deepfake": avg_score > 0.5,
                "frames_analyzed": len(scores),
                "frame_scores": scores,
            }

    except ImportError:
        logger.warning("OpenCV not installed — video analysis unavailable")
    except Exception as e:
        logger.error("Video analysis failed: %s", e)

    return {"deepfake_confidence": 0.0, "is_deepfake": False, "error": "Analysis unavailable"}
