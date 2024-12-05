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
  private apiEndpoint = config.apiEndpoint;

  async fetchHistoricalData(
    startDate: Date, 
    endDate: Date, 
    coins: string[]
  ): Promise<MarketData[]> {
    try {
      // TODO: Replace with actual API call
      const response = await fetch(`${this.apiEndpoint}/historical`, {
        method: 'POST',
        body: JSON.stringify({ startDate, endDate, coins })
      });
      
      const data = await response.json();
      return data.map((item: any): MarketData => ({
        symbol: item.symbol,
        marketCap: Number(item.market_cap),
        price: Number(item.price),
        volume24h: Number(item.volume_24h),
        timestamp: Number(item.timestamp)
      }));
    } catch (error) {
      console.error('Error fetching historical data:', error);
      return [];
    }
  }

  async calculateBTCDominance(timestamp: number): Promise<number> {
    try {
      const allCoins = await this.fetchHistoricalData(
        new Date(timestamp),
        new Date(timestamp),
        ['BTC']
      );
      
      const btcData = allCoins.find(coin => coin.symbol === 'BTC');
      const totalMarketCap = allCoins.reduce((sum, coin) => sum + coin.marketCap, 0);
      
      return btcData ? (btcData.marketCap / totalMarketCap) * 100 : 0;
    } catch (error) {
      console.error('Error calculating BTC dominance:', error);
      return 0;
    }
  }
} 