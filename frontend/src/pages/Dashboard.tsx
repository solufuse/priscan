import { useEffect, useState } from 'react';

// Define a type for our data to ensure type safety
interface Performer {
    ticker: string;
    company: string;
    price: number;
    market_cap: string;
    ps: number;
    pe: number | string;
    ytd: number;
}

const Dashboard = () => {
    const [data, setData] = useState<Performer[]>([]);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const response = await fetch('/api/dashboard/sp500-performers');
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                const performers: Performer[] = await response.json();
                setData(performers);
            } catch (err: any) {
                setError(err.message);
            }
        };

        fetchData();
    }, []);

    return (
        <div className="container mx-auto">
            <h1 className="text-3xl font-bold mb-6 text-center">S&P 500 Top Performers</h1>
            
            {error && (
                <div className="bg-red-500 text-white p-3 rounded-md text-center mb-4">
                    <p>Error: {error}</p>
                </div>
            )}

            <div className="overflow-x-auto bg-gray-800 rounded-lg shadow-lg">
                <table className="min-w-full text-sm text-left text-gray-400">
                    <thead className="text-xs text-gray-300 uppercase bg-gray-700">
                        <tr>
                            <th scope="col" className="px-6 py-3">Ticker</th>
                            <th scope="col" className="px-6 py-3">Company</th>
                            <th scope="col" className="px-6 py-3">Price</th>
                            <th scope="col" className="px-6 py-3">Market Cap</th>
                            <th scope="col" className="px-6 py-3">P/S</th>
                            <th scope="col" className="px-6 py-3">P/E</th>
                            <th scope="col" className="px-6 py-3">% YTD</th>
                        </tr>
                    </thead>
                    <tbody>
                        {data.map((stock) => (
                            <tr key={stock.ticker} className="border-b border-gray-700 hover:bg-gray-600">
                                <th scope="row" className="px-6 py-4 font-medium text-white whitespace-nowrap">
                                    {stock.ticker}
                                </th>
                                <td className="px-6 py-4">{stock.company}</td>
                                <td className="px-6 py-4">${stock.price.toFixed(2)}</td>
                                <td className="px-6 py-4">{stock.market_cap}</td>
                                <td className="px-6 py-4">{stock.ps}</td>
                                <td className="px-6 py-4">{stock.pe}</td>
                                <td className={`px-6 py-4 ${stock.ytd > 0 ? 'text-green-400' : 'text-red-400'}`}>
                                    {stock.ytd > 0 ? '+' : ''}{stock.ytd.toFixed(2)}%
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default Dashboard;
