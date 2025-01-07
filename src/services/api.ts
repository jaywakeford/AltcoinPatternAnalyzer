import { MarketData } from './DataService';

// Mock data for development
const mockData: MarketData[] = [
  { symbol: 'BTC', marketCap: 800000000000, price: 40000, volume24h: 30000000000, timestamp: Date.now() - 86400000 * 7 },
  { symbol: 'BTC', marketCap: 850000000000, price: 42000, volume24h: 32000000000, timestamp: Date.now() - 86400000 * 6 },
  { symbol: 'BTC', marketCap: 820000000000, price: 41000, volume24h: 31000000000, timestamp: Date.now() - 86400000 * 5 },
  { symbol: 'BTC', marketCap: 900000000000, price: 45000, volume24h: 35000000000, timestamp: Date.now() - 86400000 * 4 },
];

export const fetchMarketData = async (): Promise<MarketData[]> => {
  // For development, return mock data
  if (process.env.NODE_ENV === 'development') {
    return new Promise((resolve) => {
      setTimeout(() => resolve(mockData), 1000); // Simulate network delay
    });
  }

  try {
    const response = await fetch('YOUR_API_ENDPOINT');
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();
    return data as MarketData[];
  } catch (error) {
    console.error('Error fetching market data:', error);
    throw new Error('Failed to fetch market data');
  }
}; 