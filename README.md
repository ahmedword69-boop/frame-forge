# Frame Forge

A local video frame interpolation workbench. Upload a video, choose a target frame rate, and export a motion-interpolated MP4. The default 120 FPS pipeline uses FFmpeg's `minterpolate` motion-compensation filter.

## Run

1. Install FFmpeg: `brew install ffmpeg`
2. Create an environment: `python3 -m venv .venv && source .venv/bin/activate`
3. Install Python dependencies: `pip install -r requirements.txt`
4. Start the app: `uvicorn app.main:app --reload`
5. Open `http://127.0.0.1:8000`

The input and output directories are temporary working folders and are ignored by git. This first version is CPU-based. A RIFE or FILM backend can be added behind `process_job` when GPU acceleration is needed.
