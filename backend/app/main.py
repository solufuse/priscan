import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from .config import settings

app = FastAPI()

# Serve the frontend
if os.path.exists("frontend/dist"):
    app.mount("/assets", StaticFiles(directory="frontend/dist/assets"), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        # Serve index.html for paths without a file extension (client-side routing)
        if not os.path.splitext(full_path)[1] and os.path.exists("frontend/dist/index.html"):
            return FileResponse("frontend/dist/index.html")
        # Serve the requested file if it exists
        file_path = os.path.join("frontend/dist", full_path)
        if os.path.exists(file_path):
            return FileResponse(file_path)
        # Fallback to index.html for any other case (like a 404)
        if os.path.exists("frontend/dist/index.html"):
            return FileResponse("frontend/dist/index.html")
        # If even index.html doesn't exist, something is wrong with the build
        raise HTTPException(status_code=500, detail="Frontend not built or found.")

# API endpoints
@app.get("/api/stocks/{symbol}")
def get_stock_data(symbol: str):
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "TIME_SERIES_DAILY",
        "symbol": symbol,
        "apikey": settings.ALPHA_VANTAGE_API_KEY,
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        if "Error Message" in data or "Note" in data:
            error_message = data.get("Error Message", data.get("Note", f"Could not find data for symbol: {symbol}"))
            raise HTTPException(status_code=404, detail=error_message)
        return data
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error fetching data from Alpha Vantage: {e}")

# CORS for development (when frontend and backend are on different ports)
# This is not strictly necessary for the final Docker container but good for dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
