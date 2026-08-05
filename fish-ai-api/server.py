import base64
import io
import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from pathlib import Path

import cv2
import numpy as np
import torch
import yaml
from PIL import Image, ImageOps
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

MODEL_ROOT = Path(__file__).resolve().parent.parent / "fish-ai-model"
WEIGHTS = MODEL_ROOT / "trained_weight" / "20210222_efficientdet-d2_29_203900.pth"
REFERENCE_MANIFEST = MODEL_ROOT / "training-reference-manifest.json"
REFERENCE_CLASSIFIER_WEIGHTS = Path(__file__).resolve().parent / "models" / "reference_classifier.pt"
KOREAN_LABELS = ["광어", "우럭", "참돔", "감성돔", "돌돔"]
INPUT_SIZE = 768  # EfficientDet-D2
CLASSIFIER_LABELS = ["OliveFlounder", "KoreaRockfish", "RedSeabream", "BlackPorgy", "RockBream"]

sys.path.insert(0, str(MODEL_ROOT))
_model = None
_runtime_error = None
_reference_classifier = None
_reference_classifier_error = None

app = FastAPI(title="FishOn Busan AI")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://giftedu161-bit.github.io", "http://localhost:8000", "null"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)


@app.middleware("http")
async def allow_private_network(request, call_next):
    """Allow the HTTPS GitHub Pages app to call this local development API."""
    response = await call_next(request)
    response.headers["Access-Control-Allow-Private-Network"] = "true"
    return response


def load_model():
    global _model, _runtime_error
    if _model is not None:
        return _model
    if _runtime_error:
        raise RuntimeError(_runtime_error)
    try:
        from efficientdet.backbone import EfficientDetBackbone

        params = yaml.safe_load((MODEL_ROOT / "projects" / "fish_77.yml").read_text(encoding="utf-8"))
        model = EfficientDetBackbone(
            num_classes=len(params["obj_list"]),
            compound_coef=2,
            ratios=eval(params["anchors_ratios"]),
            scales=eval(params["anchors_scales"]),
        )
        checkpoint = torch.load(WEIGHTS, map_location="cpu", weights_only=False)
        target_keys = set(model.state_dict())
        compatible = {}
        for key, value in checkpoint.items():
            normalized = key.replace(".conv.", ".")
            compatible[normalized if normalized in target_keys else key] = value
        loaded = model.load_state_dict(compatible, strict=False)
        if loaded.missing_keys or loaded.unexpected_keys:
            raise RuntimeError("학습 가중치를 모델 구조에 완전히 연결하지 못했습니다.")
        model.eval()
        _model = model
        return _model
    except Exception as error:
        _runtime_error = str(error)
        raise


def prepare_image(payload: bytes):
    image = cv2.imdecode(np.frombuffer(payload, np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("사진 파일을 읽을 수 없습니다.")
    rgb = image[..., ::-1]
    normalized = (rgb / 255.0 - np.array([0.485, 0.456, 0.406])) / np.array([0.229, 0.224, 0.225])
    height, width = normalized.shape[:2]
    scale = min(INPUT_SIZE / height, INPUT_SIZE / width)
    resized = cv2.resize(normalized, (round(width * scale), round(height * scale)))
    framed = np.zeros((INPUT_SIZE, INPUT_SIZE, 3), np.float32)
    framed[: resized.shape[0], : resized.shape[1]] = resized
    tensor = torch.from_numpy(framed).unsqueeze(0).permute(0, 3, 1, 2).float()
    return tensor


def classify_reference_photo(payload: bytes):
    """Use the locally trained beta classifier only when it is more confident."""
    global _reference_classifier, _reference_classifier_error
    if not REFERENCE_CLASSIFIER_WEIGHTS.exists() or _reference_classifier_error:
        return None
    try:
        if _reference_classifier is None:
            from train_reference_classifier import IMAGE_SIZE, ReferenceFishNet
            checkpoint = torch.load(REFERENCE_CLASSIFIER_WEIGHTS, map_location="cpu", weights_only=False)
            model = ReferenceFishNet(len(checkpoint["labels"]))
            model.load_state_dict(checkpoint["state_dict"])
            model.eval()
            _reference_classifier = (model, checkpoint["labels"], checkpoint["imageSize"])
        model, labels, image_size = _reference_classifier
        image = Image.open(io.BytesIO(payload)).convert("RGB")
        image = ImageOps.fit(image, (image_size, image_size), method=Image.Resampling.BILINEAR)
        pixels = np.asarray(image, dtype=np.float32).transpose(2, 0, 1) / 255.0
        tensor = (torch.from_numpy(pixels) - torch.tensor([.485, .456, .406])[:, None, None]) / torch.tensor([.229, .224, .225])[:, None, None]
        with torch.no_grad():
            probabilities = torch.softmax(model(tensor.unsqueeze(0)), dim=1)[0]
        index = int(torch.argmax(probabilities).item())
        return {"label": labels[index], "confidence": float(probabilities[index].item())}
    except Exception as error:
        _reference_classifier_error = str(error)
        return None


def training_reference_summary():
    """Return the labelled beta photos that are ready for annotation/training."""
    try:
        manifest = json.loads(REFERENCE_MANIFEST.read_text(encoding="utf-8"))
        names = manifest.get("species", {})
        counts = {}
        for label, _ in manifest.get("samples", []):
            counts[label] = counts.get(label, 0) + 1
        return {
            "sampleCount": sum(counts.values()),
            "speciesCount": len(counts),
            "bySpecies": [{"label": label, "name": names.get(label, label), "count": count}
                          for label, count in counts.items()],
            "status": "prepared_for_annotation",
        }
    except (OSError, ValueError, TypeError):
        return {"sampleCount": 0, "speciesCount": 0, "bySpecies": [], "status": "unavailable"}


@app.get("/health")
def health():
    try:
        load_model()
        return {"ready": True, "model": "EfficientDet-D2", "species": KOREAN_LABELS, "device": "CPU", "trainingReferences": training_reference_summary()}
    except Exception as error:
        return {"ready": False, "model": "EfficientDet-D2", "species": KOREAN_LABELS, "error": str(error)}


@app.get("/training-references")
def training_references():
    """Expose only aggregate training status; source photos remain local."""
    return training_reference_summary()


@app.get("/gemini-health")
def gemini_health():
    return {"ready": bool(os.environ.get("GEMINI_API_KEY")), "model": "gemini-2.5-flash"}


@app.post("/analyze-gemini")
async def analyze_gemini(image: UploadFile = File(...)):
    """Optional Gemini second opinion. The key stays only on the local AI server."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return {"status": "unavailable", "message": "Gemini API 키가 서버에 설정되지 않았습니다."}
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(400, "이미지 파일만 분석할 수 있습니다.")
    payload = await image.read()
    if len(payload) > 12 * 1024 * 1024:
        raise HTTPException(413, "사진은 12MB 이하로 올려주세요.")
    prompt = (
        "You verify a Korean sea fishing photo. Return JSON only with keys fish_present, species, confidence, reason. "
        "species must be exactly one of 광어, 우럭, 참돔, 감성돔, 돌돔, or null. "
        "confidence must be a number from 0 to 1. Do not guess when the fish is unclear."
    )
    body = {"contents": [{"parts": [{"text": prompt}, {"inline_data": {"mime_type": image.content_type, "data": base64.b64encode(payload).decode("ascii")}}]}], "generationConfig": {"temperature": 0, "responseMimeType": "application/json"}}
    request = Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}",
        data=json.dumps(body).encode("utf-8"), headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urlopen(request, timeout=35) as response:
            response_data = json.loads(response.read().decode("utf-8"))
        text = response_data["candidates"][0]["content"]["parts"][0]["text"].strip().removeprefix("```json").removesuffix("```").strip()
        result = json.loads(text)
        species = result.get("species") if result.get("species") in KOREAN_LABELS else None
        confidence = max(0, min(1, float(result.get("confidence", 0))))
        return {"status": "ready", "species": species, "confidence": confidence, "message": f"Gemini 2차 판별: {result.get('reason', '')}"}
    except HTTPError as error:
        try:
            provider_message = json.loads(error.read().decode("utf-8")).get("error", {}).get("message", str(error))
        except Exception:
            provider_message = str(error)
        return {"status": "unavailable", "message": f"Gemini 2차 판별을 사용할 수 없습니다: {provider_message}"}
    except (URLError, KeyError, ValueError, json.JSONDecodeError) as error:
        return {"status": "unavailable", "message": f"Gemini 2차 판별을 사용할 수 없습니다: {error}"}


@app.post("/analyze")
async def analyze(image: UploadFile = File(...)):
    if not WEIGHTS.exists():
        raise HTTPException(503, "모델 가중치 파일을 찾을 수 없습니다.")
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(400, "이미지 파일만 분석할 수 있습니다.")
    payload = await image.read()
    if len(payload) > 12 * 1024 * 1024:
        raise HTTPException(413, "사진은 12MB 이하로 올려주세요.")
    try:
        from efficientdet.utils import BBoxTransform, ClipBoxes
        from utils.utils import postprocess_with_KP

        model = load_model()
        tensor = prepare_image(payload)
        with torch.no_grad():
            _, regression, classification, anchors, regression_kp = model(tensor)
            predictions = postprocess_with_KP(
                tensor, anchors, regression, regression_kp, classification,
                BBoxTransform(), ClipBoxes(), 0.20, 0.20,
            )[0]
        if len(predictions.get("scores", [])) == 0:
            return {"status": "ready", "species": None, "confidence": 0, "message": "물고기를 찾지 못했습니다. 물고기가 잘 보이게 다시 촬영해주세요."}
        best_index = int(np.argmax(predictions["scores"]))
        class_id = int(predictions["class_ids"][best_index])
        confidence = float(predictions["scores"][best_index])
        species = KOREAN_LABELS[class_id] if 0 <= class_id < len(KOREAN_LABELS) else None
        message = "AI Hub detector result"
        reference = classify_reference_photo(payload)
        if reference and reference["confidence"] > confidence:
            reference_index = CLASSIFIER_LABELS.index(reference["label"])
            species = KOREAN_LABELS[reference_index]
            confidence = reference["confidence"]
            message = "FishOn 40-photo reference classifier result"
        return {
            "status": "ready",
            "species": species,
            "confidence": confidence,
            "message": message,
        }
    except ValueError as error:
        raise HTTPException(400, str(error))
    except Exception as error:
        raise HTTPException(503, f"AI 모델 분석을 시작하지 못했습니다: {error}")
