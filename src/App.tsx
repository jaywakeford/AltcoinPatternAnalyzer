import React, { useState } from 'react';
import WaterfallChart from './components/WaterfallChart';
import { MarketData } from './services/DataService';

const App: React.FC = () => {
  const [error, setError] = useState<string | null>(null);

  const sampleData: MarketData[] = [
    { symbol: 'BTC', marketCap: 800000000000, price: 40000, volume24h: 30000000000, timestamp: Date.now() - 86400000 * 7 },
    { symbol: 'BTC', marketCap: 850000000000, price: 42000, volume24h: 32000000000, timestamp: Date.now() - 86400000 * 6 },
    { symbol: 'BTC', marketCap: 820000000000, price: 41000, volume24h: 31000000000, timestamp: Date.now() - 86400000 * 5 },
    { symbol: 'BTC', marketCap: 900000000000, price: 45000, volume24h: 35000000000, timestamp: Date.now() - 86400000 * 4 },
    { symbol: 'BTC', marketCap: 880000000000, price: 44000, volume24h: 33000000000, timestamp: Date.now() - 86400000 * 3 },
    { symbol: 'BTC', marketCap: 920000000000, price: 46000, volume24h: 36000000000, timestamp: Date.now() - 86400000 * 2 },
    { symbol: 'BTC', marketCap: 1000000000000, price: 50000, volume24h: 40000000000, timestamp: Date.now() - 86400000 },
  ];

  const handleSequenceSelect = (sequence: string[]): void => {
    try {
      console.log('Selected sequence:', sequence);
      // Add your sequence analysis logic here
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    }
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>Crypto Waterfall Analyzer</h1>
        {error && (
          <div className="error-message">
            {error}
            <button onClick={() => setError(null)}>Dismiss</button>
          </div>
        )}
      </header>
      <main>
        <WaterfallChart 
          data={sampleData}
          selectedCohort="all"
          onSequenceSelect={handleSequenceSelect}
        />
      </main>
    </div>
  );
};

export default App; 