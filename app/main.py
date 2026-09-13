from pathlib import Path
import asyncio
import json
import shutil
import subprocess
import uuid

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).resolve().parent.parent
INPUT_DIR = ROOT / "input"
OUTPUT_DIR = ROOT / "output"
INPUT_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

app = FastAPI(title="Frame Forge")
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")
jobs: dict[str, dict] = {}


@app.get("/")
def index() -> FileResponse:
    return FileResponse(ROOT / "static" / "index.html")


@app.post("/api/jobs")
async def create_job(file: UploadFile = File(...), target_fps: int = 120):
    if target_fps not in (60, 90, 120, 144, 240):
        raise HTTPException(400, "Choose a supported target FPS.")
    if not file.filename or not file.content_type or not file.content_type.startswith("video/"):
        raise HTTPException(400, "Upload a video file.")

    job_id = uuid.uuid4().hex
    suffix = Path(file.filename).suffix.lower() or ".mp4"
    input_path = INPUT_DIR / f"{job_id}{suffix}"
    output_path = OUTPUT_DIR / f"{job_id}.mp4"
    with input_path.open("wb") as destination:
        shutil.copyfileobj(file.file, destination)

    jobs[job_id] = {"status": "queued", "progress": 0, "target_fps": target_fps}
    asyncio.create_task(process_job(job_id, input_path, output_path, target_fps))
    return {"id": job_id}

@app.get("/api/jobs/{job_id}")
def job_status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(404, "Job not found.")
    return jobs[job_id]

@app.get("/api/jobs/{job_id}/download")
def download(job_id: str):
    job = jobs.get(job_id)
    output_path = OUTPUT_DIR / f"{job_id}.mp4"
    if not job or job["status"] != "complete" or not output_path.exists():
        raise HTTPException(404, "Output is not ready.")
    return FileResponse(output_path, media_type="video/mp4", filename="frame-forge-120fps.mp4")


async def process_job(job_id: str, input_path: Path, output_path: Path, target_fps: int):
    jobs[job_id]["status"] = "processing"
    jobs[job_id]["progress"] = 8
    command = [
        "ffmpeg", "-y", "-i", str(input_path),
        "-vf", f"minterpolate=fps={target_fps}:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-c:a", "aac", "-movflags", "+faststart", str(output_path),
    ]
    try:
        process = await asyncio.create_subprocess_exec(
            *command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        _, stderr = await process.communicate()
        if process.returncode != 0:
            message = stderr.decode(errors="replace")[-500:]
            jobs[job_id] = {"status": "error", "progress": 0, "message": message}
            return
        jobs[job_id] = {"status": "complete", "progress": 100, "target_fps": target_fps}
    except FileNotFoundError:
        jobs[job_id] = {
            "status": "error",
            "progress": 0,
            "message": "FFmpeg is not installed. Install it with: brew install ffmpeg",
        }
    finally:
        input_path.unlink(missing_ok=True)
        output_path.unlink(missing_ok=False)
    if output_path.exists():
        jobs[job_id] = {"status": "complete", "progress": 100, "target_fps": target_fps}
        

