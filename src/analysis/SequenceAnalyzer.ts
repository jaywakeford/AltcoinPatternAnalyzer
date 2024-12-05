import { MarketData } from '../services/DataService';

export interface SequenceResult {
  altcoinSequence: string[];
  entryPoints: number[];
  exitPoints: number[];
  expectedGains: number[];
}

export class SequenceAnalyzer {
  private readonly GAIN_THRESHOLD = 10; // 10% gain threshold

  analyzeHistoricalSequences(
    btcDominanceThreshold: number,
    historicalData: MarketData[]
  ): SequenceResult {
    const result: SequenceResult = {
      altcoinSequence: [],
      entryPoints: [],
      exitPoints: [],
      expectedGains: []
    };

    // Group data by timestamp
    const groupedData = this.groupDataByTimestamp(historicalData);
    
    // Find sequences where BTC dominance decreases
    const timestamps = Object.keys(groupedData).sort();
    
    for (let i = 1; i < timestamps.length; i++) {
      const currentTime = timestamps[i];
      const prevTime = timestamps[i - 1];
      
      const currentData = groupedData[currentTime];
      const prevData = groupedData[prevTime];
      
      // If BTC dominance decreased
      if (this.calculateBTCDominance(currentData) < btcDominanceThreshold) {
        const gainers = this.findTopGainers(prevData, currentData);
        
        if (gainers.length > 0) {
          result.altcoinSequence.push(gainers[0].symbol);
          result.entryPoints.push(Number(prevTime));
          result.exitPoints.push(Number(currentTime));
          result.expectedGains.push(gainers[0].gain);
        }
      }
    }

    return result;
  }

  private groupDataByTimestamp(data: MarketData[]): Record<string, MarketData[]> {
    return data.reduce((acc, item) => {
      const timestamp = item.timestamp.toString();
      if (!acc[timestamp]) {
        acc[timestamp] = [];
      }
      acc[timestamp].push(item);
      return acc;
    }, {} as Record<string, MarketData[]>);
  }

  private calculateBTCDominance(data: MarketData[]): number {
    const btcData = data.find(coin => coin.symbol === 'BTC');
    const totalMarketCap = data.reduce((sum, coin) => sum + coin.marketCap, 0);
    return btcData ? (btcData.marketCap / totalMarketCap) * 100 : 0;
  }

  private findTopGainers(
    prevData: MarketData[], 
    currentData: MarketData[]
  ): Array<{ symbol: string; gain: number }> {
    const gains = currentData.map(current => {
      const prev = prevData.find(p => p.symbol === current.symbol);
      if (!prev) return { symbol: current.symbol, gain: 0 };
      
      const gain = ((current.price - prev.price) / prev.price) * 100;
      return { symbol: current.symbol, gain };
    });

    return gains
      .filter(item => item.gain > this.GAIN_THRESHOLD)
      .sort((a, b) => b.gain - a.gain);
  }
} 