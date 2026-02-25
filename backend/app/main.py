import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
import yfinance as yf
import pandas as pd

from .config import settings
from .routers import dashboard

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Data Transformation ---

def transform_yfinance_to_alphavantage(df: pd.DataFrame) -> dict:
    """
    Transforms a yfinance DataFrame to the Alpha Vantage TIME_SERIES_DAILY format.
    """
    time_series_daily = {}
    for index, row in df.iterrows():
        date_str = index.strftime('%Y-%m-%d')
        time_series_daily[date_str] = {
            "1. open": str(row['Open']),
            "2. high": str(row['High']),
            "3. low": str(row['Low']),
            "4. close": str(row['Close']),
            "5. volume": str(row['Volume'])
        }
    return {"Time Series (Daily)": time_series_daily}

# --- API Fetchers ---

async def fetch_from_alpha_vantage(symbol: str):
    """Fetches stock data from Alpha Vantage."""
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
        # Alpha Vantage sends a "Note" when the API limit is hit.
        if "Note" in data or "Error Message" in data:
            # This is considered a failure, so we can try the next provider.
            raise ValueError(data.get("Note") or data.get("Error Message"))
        return data
    except (requests.exceptions.RequestException, ValueError, KeyError) as e:
        print(f"Alpha Vantage failed: {e}")
        return None

async def fetch_from_yfinance(symbol: str):
    """Fetches stock data from Yahoo Finance."""
    try:
        ticker = yf.Ticker(symbol)
        # Get historical data for a reasonable period
        hist = ticker.history(period="5y") 
        if hist.empty:
            raise ValueError("No data found for symbol")
        
        # Transform the data to the expected format
        return transform_yfinance_to_alphavantage(hist)
    except Exception as e:
        print(f"Yahoo Finance failed: {e}")
        return None

# --- API Endpoint ---
app.include_router(dashboard.router)

@app.get("/api/stocks/{symbol}")
async def get_stock_data(symbol: str):
    """
    Tries to fetch stock data from multiple providers in a fallback sequence.
    """
    # 1. Try Alpha Vantage
    data = await fetch_from_alpha_vantage(symbol)
    if data:
        print("Fetched data from Alpha Vantage")
        return data

    # 2. Fallback to Yahoo Finance
    data = await fetch_from_yfinance(symbol)
    if data:
        print("Fetched data from Yahoo Finance")
        return data
        
    # If all providers fail
    raise HTTPException(status_code=500, detail="All data providers failed to return data for the symbol.")


# --- Static File Serving ---
if os.path.exists("frontend/dist"):
    app.mount("/assets", StaticFiles(directory="frontend/dist/assets"), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        return FileResponse("frontend/dist/index.html")
