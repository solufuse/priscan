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
    # Add your production domain here
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "https://price.solufuse.com"],
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
        return response.json()
    except (requests.exceptions.RequestException, KeyError) as e:
        print(f"Alpha Vantage request failed: {e}")
        return None

async def fetch_from_yfinance(symbol: str):
    """Fetches stock data from Yahoo Finance."""
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="5y") 
        if hist.empty:
            raise ValueError("No data found for symbol in yfinance")
        return transform_yfinance_to_alphavantage(hist)
    except Exception as e:
        print(f"Yahoo Finance failed: {e}")
        return None

# --- API Endpoints (all prefixed with /api) ---
app.include_router(dashboard.router) # Has prefix /api/dashboard

@app.get("/api/stocks/{symbol}")
async def get_stock_data(symbol: str):
    """
    Tries to fetch stock data from multiple providers in a fallback sequence.
    """
    # 1. Try Alpha Vantage
    data = await fetch_from_alpha_vantage(symbol)
    
    # Robust check: Ensure "Time Series (Daily)" key exists and its value is not None/empty.
    if data and data.get("Time Series (Daily)"):
        print("Fetched data from Alpha Vantage")
        return data

    print("Alpha Vantage failed or returned invalid data, falling back to Yahoo Finance.")

    # 2. Fallback to Yahoo Finance
    data = await fetch_from_yfinance(symbol)
    if data and data.get("Time Series (Daily)"):
        print("Fetched data from Yahoo Finance")
        return data
        
    # If all providers fail
    raise HTTPException(status_code=500, detail=f"All data providers failed for symbol {symbol}.")


# --- Static File Serving for SPA (mount this LAST) ---
class SPAStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        try:
            # Try to get the file from the static directory
            return await super().get_response(path, scope)
        except HTTPException as ex:
            # If the file is not found, serve index.html
            if ex.status_code == 404:
                return await super().get_response("index.html", scope)
            else:
                raise ex

# This path is relative to the WORKDIR defined in the Dockerfile
frontend_dist_path = "frontend/dist"
if os.path.exists(frontend_dist_path):
    print(f"Serving frontend from: {frontend_dist_path}")
    app.mount("/", SPAStaticFiles(directory=frontend_dist_path), name="spa")
else:
    print(f"[ERROR] Frontend build directory not found at: {frontend_dist_path}. Current dir: {os.getcwd()}")

