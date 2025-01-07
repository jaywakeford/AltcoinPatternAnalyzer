import config from '../config/config';

// Types
export interface MarketData {
  symbol: string;
  marketCap: number;
  price: number;
  volume24h: number;
  timestamp: number;
}

// Service class
export class CryptoDataService {
  private baseUrl: string;

  constructor(baseUrl: string = 'https://api.binance.com') {
    this.baseUrl = baseUrl;
  }

  async fetchMarketData(symbol: string = 'BTC'): Promise<MarketData[]> {
    try {
      // For development, return mock data
      if (process.env.NODE_ENV === 'development') {
        return this.getMockData(symbol);
      }

      const response = await fetch(`${this.baseUrl}/api/v3/klines?symbol=${symbol}USDT&interval=1d&limit=30`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      
      return data.map((item: any) => ({
        symbol,
        timestamp: item[0],
        price: parseFloat(item[4]),
        volume24h: parseFloat(item[5]),
        marketCap: parseFloat(item[4]) * parseFloat(item[5]) // Approximate market cap
      }));
    } catch (error) {
      console.error('Error fetching market data:', error);
      return this.getMockData(symbol);
    }
  }

  private getMockData(symbol: string): MarketData[] {
    const now = Date.now();
    const dayInMs = 86400000;
    
    return Array.from({ length: 30 }, (_, i) => ({
      symbol,
      timestamp: now - (29 - i) * dayInMs,
      price: 40000 + Math.random() * 5000,
      volume24h: 30000000000 + Math.random() * 5000000000,
      marketCap: 800000000000 + Math.random() * 50000000000
    }));
  }
} 