# Fish AI API

Run this service on a CUDA-capable Windows PC with the extracted `fish-ai-model` directory next to this folder.

```powershell
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
.\.venv\Scripts\uvicorn server:app --host 0.0.0.0 --port 8000
```

The model recognizes OliveFlounder, KoreaRockfish, RedSeabream, BlackPorgy, and RockBream.
