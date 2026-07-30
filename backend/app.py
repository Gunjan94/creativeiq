"""
app.py — local FastAPI server wrapping the Lambda-shaped handlers.

Run:  uvicorn app:app --reload --port 8000   (from backend/)
Routes mirror the API Gateway endpoints:
  GET  /catalog
  GET  /segments
  POST /predict
  POST /generate         -> SSE stream (copy deltas + image + done)
  POST /generate/summary -> non-streaming JSON (for tests / quick checks)
  GET  /data/...         -> serves bundled synthetic assets (catalog/hero/generated images)
  GET  /health
"""
import json
import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse, Response

from handlers import catalog as catalog_h
from handlers import segments as segments_h
from handlers import predict as predict_h
from handlers import generate as generate_h
from handlers import campaigns as campaigns_h
from handlers import analytics as analytics_h
from core import data, bedrock

app = FastAPI(title="CreativeIQ", version="1.0.0")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"ok": True, "use_bedrock": bedrock.available(),
            "region": bedrock.REGION, "mode": "live" if bedrock.available() else "offline"}


@app.get("/catalog")
def catalog():
    return catalog_h.get_catalog()


@app.get("/segments")
def segments():
    return segments_h.get_segments()


@app.get("/campaigns")
def campaigns(limit: int = 60):
    return campaigns_h.get_campaigns(limit)


@app.get("/analytics")
def analytics():
    return analytics_h.get_analytics()


@app.get("/comparable")
def comparable(segment_id: str, format: str = None, image_style: str = None, copy_tone: str = None):
    return analytics_h.get_comparable(segment_id, format, image_style, copy_tone)


@app.post("/predict")
async def predict(request: Request):
    body = await request.json()
    return predict_h.predict(body)


@app.post("/generate/summary")
async def generate_summary(request: Request):
    body = await request.json()
    return generate_h.generate_summary(body)


@app.post("/generate")
async def generate(request: Request):
    body = await request.json()

    def event_stream():
        for evt in generate_h.generate_events(body):
            yield f"event: {evt['event']}\ndata: {json.dumps(evt['data'])}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.get("/data/{path:path}")
def serve_data(path: str):
    full = os.path.normpath(os.path.join(data.DATA_DIR, path))
    if not full.startswith(os.path.abspath(data.DATA_DIR)):
        return JSONResponse({"error": "forbidden"}, status_code=403)
    if not os.path.isfile(full):
        return JSONResponse({"error": "not found"}, status_code=404)
    if full.endswith(".svg"):
        with open(full, "r") as f:
            return Response(content=f.read(), media_type="image/svg+xml")
    return FileResponse(full)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))
