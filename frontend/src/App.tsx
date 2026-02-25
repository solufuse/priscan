import { useState, useRef, useEffect } from 'react';
import { createChart, IChartApi, ISeriesApi, CandlestickData } from 'lightweight-charts';
import './App.css';

function App() {
    const [symbol, setSymbol] = useState('AAPL');
    const [error, setError] = useState<string | null>(null);

    const chartContainerRef = useRef<HTMLDivElement>(null);
    const chartRef = useRef<IChartApi | null>(null);
    const candlestickSeriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);

    const fetchData = async (ticker: string) => {
        setError(null);
        try {
            const response = await fetch(`http://localhost:8000/api/stocks/${ticker}`);
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to fetch stock data');
            }
            const data = await response.json();
            const timeSeries = data["Time Series (Daily)"];

            if (!timeSeries) {
                throw new Error('Invalid data format from API. Check the symbol.');
            }

            const chartData: CandlestickData[] = Object.keys(timeSeries).map(date => ({
                time: date,
                open: parseFloat(timeSeries[date]["1. open"]),
                high: parseFloat(timeSeries[date]["2. high"]),
                low: parseFloat(timeSeries[date]["3. low"]),
                close: parseFloat(timeSeries[date]["4. close"]),
            })).sort((a, b) => new Date(a.time as string).getTime() - new Date(b.time as string).getTime());

            if (candlestickSeriesRef.current) {
                candlestickSeriesRef.current.setData(chartData);
                chartRef.current?.timeScale().fitContent();
            }

        } catch (err: any) {
            setError(err.message);
            console.error(err);
        }
    };

    useEffect(() => {
        if (chartContainerRef.current && !chartRef.current) {
            chartRef.current = createChart(chartContainerRef.current, {
                width: chartContainerRef.current.clientWidth,
                height: 500,
                layout: {
                    background: { color: '#1a1e26' },
                    textColor: '#d1d4dc',
                },
                grid: {
                    vertLines: { color: '#2e333e' },
                    horzLines: { color: '#2e333e' },
                },
            });
            candlestickSeriesRef.current = chartRef.current.addCandlestickSeries();
        }

        fetchData(symbol); // Fetch initial data for AAPL

        const handleResize = () => {
            if (chartRef.current && chartContainerRef.current) {
                chartRef.current.resize(chartContainerRef.current.clientWidth, 500);
            }
        };

        window.addEventListener('resize', handleResize);

        return () => {
            window.removeEventListener('resize', handleResize);
            if (chartRef.current) {
                chartRef.current.remove();
                chartRef.current = null;
            }
        };
    }, []); // Run only once on mount

    const handleSymbolChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setSymbol(e.target.value.toUpperCase());
    };

    const handleFetchData = (e: React.FormEvent) => {
        e.preventDefault();
        if (symbol) {
            fetchData(symbol);
        }
    };

    return (
        <div className="min-h-screen bg-gray-900 text-white p-4">
            <div className="container mx-auto">
                <h1 className="text-3xl font-bold mb-4 text-center">Stock Price Tracker</h1>
                <form onSubmit={handleFetchData} className="flex justify-center mb-4">
                    <input
                        type="text"
                        value={symbol}
                        onChange={handleSymbolChange}
                        className="p-2 rounded-l-md bg-gray-800 border border-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="Enter stock symbol (e.g., AAPL)"
                    />
                    <button
                        type="submit"
                        className="p-2 bg-blue-600 rounded-r-md hover:bg-blue-700 font-bold"
                    >
                        Get Data
                    </button>
                </form>

                {error && (
                    <div className="bg-red-500 text-white p-3 rounded-md text-center mb-4">
                        <p>Error: {error}</p>
                    </div>
                )}

                <div className="bg-gray-800 p-4 rounded-lg shadow-lg">
                    <h2 className="text-2xl font-semibold mb-2 text-center">{symbol}</h2>
                    <div ref={chartContainerRef} style={{ width: '100%', height: '500px' }} />
                </div>
            </div>
        </div>
    );
}

export default App;
