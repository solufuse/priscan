import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from .config import settings

app = FastAPI()

# CORS must be added before any routes.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- API Endpoints ---
# API routes MUST be declared before the static file serving routes.
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
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
        data = response.json()
        if "Error Message" in data or "Note" in data:
            error_message = data.get("Error Message", data.get("Note", f"Could not find data for symbol: {symbol}"))
            raise HTTPException(status_code=404, detail=error_message)
        return data
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error fetching data from Alpha Vantage: {e}")
    except Exception as e:
        # Catch any other potential errors, e.g., if response is not JSON
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

# --- Static File Serving ---
# This must come AFTER all API routes to act as a fallback.
if os.path.exists("frontend/dist"):
    # Mount the 'assets' directory which contains JS, CSS, etc.
    app.mount("/assets", StaticFiles(directory="frontend/dist/assets"), name="assets")

    # A "catch-all" route to serve index.html for any path not matched above.
    # This is crucial for client-side routing in SPAs like React.
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        return FileResponse("frontend/dist/index.html")
