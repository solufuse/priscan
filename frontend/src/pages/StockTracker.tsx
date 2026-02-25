import { useState, useRef, useEffect } from 'react';
// Correctly import types with the `type` keyword
import { createChart, type IChartApi, type ISeriesApi, type CandlestickData } from 'lightweight-charts';
import { Input } from '../components/ui/input';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';

const StockTracker = () => {
    const [symbol, setSymbol] = useState('AAPL');
    const [error, setError] = useState<string | null>(null);

    const chartContainerRef = useRef<HTMLDivElement>(null);
    const chartRef = useRef<IChartApi | null>(null);
    const candlestickSeriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);

    const fetchData = async (ticker: string) => {
        setError(null);
        try {
            const response = await fetch(`/api/stocks/${ticker}`);
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to fetch stock data');
            }
            const data = await response.json();

            const timeSeries = data["Time Series (Daily)"];
            if (!timeSeries) {
                const errorMessage = data["Note"] || 'Invalid data format from API. Check the symbol or API key limit.';
                throw new Error(errorMessage);
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

        fetchData(symbol);

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
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []); 

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
        <div className="container mx-auto p-4">
            <h1 className="text-3xl font-bold mb-4 text-center">Stock Price Tracker</h1>
            <form onSubmit={handleFetchData} className="flex justify-center mb-4 items-center gap-2">
                <Input
                    type="text"
                    value={symbol}
                    onChange={handleSymbolChange}
                    placeholder="Enter stock symbol (e.g., AAPL)"
                    className="w-1/4"
                />
                <Button type="submit">Get Data</Button>
            </form>

            {error && (
                <div className="bg-red-500 text-white p-3 rounded-md text-center mb-4">
                    <p>Error: {error}</p>
                </div>
            )}

            <Card>
                <CardHeader>
                    <CardTitle className="text-center">{symbol}</CardTitle>
                </CardHeader>
                <CardContent>
                    <div ref={chartContainerRef} style={{ width: '100%', height: '500px' }} />
                </CardContent>
            </Card>
        </div>
    );
};

export default StockTracker;
