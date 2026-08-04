from pathlib import Path
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

MODEL_ROOT = Path(__file__).resolve().parent.parent / "fish-ai-model"
WEIGHTS = MODEL_ROOT / "trained_weight" / "20210222_efficientdet-d2_29_203900.pth"
LABELS = ["광어", "우럭", "참돔", "감성돔", "돌돔"]

app = FastAPI(title="FishOn Busan AI")
app.add_middleware(CORSMiddleware, allow_origins=["https://giftedu161-bit.github.io", "http://localhost:8000"], allow_methods=["POST", "GET"], allow_headers=["*"])

@app.get("/health")
def health():
    return {"ready": WEIGHTS.exists(), "model": "EfficientDet-D2", "species": LABELS}

@app.post("/analyze")
async def analyze(image: UploadFile = File(...)):
    if not WEIGHTS.exists():
        raise HTTPException(503, "모델 가중치 파일을 찾을 수 없습니다.")
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(400, "이미지 파일만 분석할 수 있습니다.")
    payload = await image.read()
    if len(payload) > 12 * 1024 * 1024:
        raise HTTPException(413, "사진은 12MB 이하로 올려주세요.")
    # The official EfficientDet inference adapter is loaded in the next runtime step.
    # Keep the API contract stable for the web client.
    return {"status": "model-runtime-pending", "species": None, "confidence": 0, "message": "GPU 모델 런타임을 시작하면 실제 분석이 활성화됩니다."}
