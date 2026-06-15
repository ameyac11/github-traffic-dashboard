"""
api.py
This file powers the FastAPI backend, serving our data and React dashboard to the browser!
"""
import os
from pathlib import Path
from fastapi import FastAPI, HTTPException, Header, Body, File, UploadFile
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd

from github_traffic.core import validate_token, fetch_all_traffic
from github_traffic.process import process_uploaded_csv

app = FastAPI(title="GitHub Traffic API")

# Allow CORS for local development (Vite runs on 5173 usually)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/auth")
def auth(token: str = Body(..., embed=True)):
    ok, username, avatar_url, name = validate_token(token)
    if not ok:
        raise HTTPException(status_code=401, detail=username)  # validate_token returns error msg in username slot
    return {
        "authenticated": True,
        "username": username,
        "name": name or username,
        "avatar_url": avatar_url
    }

@app.post("/api/traffic")
def get_traffic(token: str = Body(..., embed=True)):
    ok, _, _, _ = validate_token(token)
    if not ok:
        raise HTTPException(status_code=401, detail="Invalid token")
        
    df = fetch_all_traffic(token)
    # Convert dataframe to JSON response
    # Replacing NaN/Inf with None so it serializes correctly to JSON
    df = df.replace([float('inf'), float('-inf')], None).where(pd.notnull(df), None)
    return df.to_dict(orient="records")

@app.post("/api/upload-csv")
def upload_csv(file: UploadFile = File(...)):
    try:
        df = process_uploaded_csv(file.file)
        df = df.replace([float('inf'), float('-inf')], None).where(pd.notnull(df), None)
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Mount the React frontend assets (if built)
frontend_dist = Path(__file__).parent / "frontend" / "dist"

@app.get("/")
def serve_index():
    index_file = frontend_dist / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return JSONResponse(
        status_code=404,
        content={"error": "Frontend not built. Run 'npm run build' in the frontend directory."}
    )

# Mount all other static files
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=frontend_dist), name="static")

