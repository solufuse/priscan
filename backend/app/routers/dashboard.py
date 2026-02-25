from fastapi import APIRouter

router = APIRouter(
    prefix="/api/dashboard",
    tags=["dashboard"],
)

# Mock data based on the user's image
mock_dashboard_data = [
    {"ticker": "MRNA", "company": "Moderna", "price": 49.70, "market_cap": "19.5B", "ps": 10.03, "pe": "n/a", "ytd": 66.61},
    {"ticker": "GNRC", "company": "Generac", "price": 227.47, "market_cap": "13.4B", "ps": 3.18, "pe": 43.28, "ytd": 64.86},
    {"ticker": "WDC", "company": "Western Digital", "price": 284.67, "market_cap": "97.2B", "ps": 9.06, "pe": 28.57, "ytd": 60.65},
    {"ticker": "TER", "company": "Teradyne", "price": 315.90, "market_cap": "49.4B", "ps": 15.48, "pe": 91.07, "ytd": 58.51},
    {"ticker": "GLW", "company": "Corning", "price": 129.99, "market_cap": "112.5B", "ps": 7.20, "pe": 70.94, "ytd": 46.22},
    {"ticker": "STX", "company": "Seagate", "price": 408.97, "market_cap": "88.9B", "ps": 8.84, "pe": 46.20, "ytd": 45.04},
]

@router.get("/sp500-performers")
async def get_sp500_performers():
    # In the future, this will fetch real data from an API like Financial Modeling Prep
    return mock_dashboard_data
