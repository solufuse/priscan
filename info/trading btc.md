yesterday someone leaked a full quant trading system on GitHub

before they deleted it i forked everything

5,000 lines of code. 7 modules. 25 mathematical factors

funds use this system to manage millions

i studied it for a week. then pointed it at crypto markets on polymarket

here's the full breakdown 
you can feed this to your claude and build the same thing

for just $200

ARCHITECTURE:

Python thinks, analyzes, calculates 
C++ executes orders in 5-10ms

data → factors → AI → strategy → risk → execution

DATA. 4 streams simultaneously:

- Binance WebSocket: prices every second, orderbook at 20 levels
- AlphaVantage: news with sentiment score from -1 to +1
-X: mention volume, engagement, influencer activity
- On-chain: BTC flows to/from exchanges

cache in Redis (<1ms). history in TimescaleDB

FACTORS:

the system calculates 25+ factors every 5 minutes: 
- price momentum over 1.5 hours 
- acceleration = momentum_30m - momentum_1h 
- RSI(14): above 70 = overbought, below 30 = oversold
- MACD: fast EMA(12) minus slow EMA(26)

microstructure: 
- Order Flow Imbalance = (buy volume - sell volume) / total. above +0.3 = strong buyer pressure 
- VPIN = |buy_vol - sell_vol| / total. above 0.75 = smart money is moving

volatility: 
- VaR(95%) = mean - 1.645 × std. answers: "what's my max loss in 95% of cases?"
- Sharpe = (return - risk free) / volatility. above 1.0 = good. above 2.0 = excellent

every factor converted to z-score and combined:

Composite Score = Σ (weight × z_score)
top 25 assets by score go to work

AI:

ClowdBot reads every news article and returns JSON

every historical article stored as a 384-dimensional vector

PROBABILITY MODEL

Geometric Brownian Motion:
P(BTC > target price) = N(d1) d1 = [ln(current/target) + (σ²/2)T] / (σ√T)

then 4 adjustments on top:
- momentum: +/-5% 
- AI sentiment: +/-7% 
- order flow: +/-2% 
- historical patterns: +/-8%

compare final probability against polymarket price if edge > 10%: enter

RISK

- Quarter Kelly for position sizing 
- max 5% bankroll per trade 
- drawdown 15% = bot stops 
- VaR < 3% per day 
- correlation between positions < 0.7 
- never take more than 1% of market liquidity

key insight is don't hold to expiry. trade the movement, not the outcome

cost: 
→ Binance API: free 
→ OpenAI: $50-100/month 
→ AWS EC2: $120/month 
→ monitoring: free

- total: $200-300/month -

code is open source. formulas above. you already have claude

the only thing between you and a working system is one free evening