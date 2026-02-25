import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .config import settings

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"]- # In production, you should restrict this to your frontend's domain
    allow_credentials=True,
    allow_methods=["*"]-,
    allow_headers=["*"]-,
)


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
        response.raise_for_status()  # Raise an exception for bad status codes
        data = response.json()
        if "Error Message" in data:
            raise HTTPException(status_code=404, detail=f"Could not find data for symbol: {symbol}")
        return data
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error fetching data from Alpha Vantage: {e}")


@app.get("/")
def read_root():
    return {"message": "Portfolio Analysis API is running"}
