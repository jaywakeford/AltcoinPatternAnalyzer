import React, { useState, useEffect } from 'react';
import WaterfallChart from './components/WaterfallChart';
import { MarketData } from './services/DataService';
import { fetchMarketData } from './services/api'; // You'll need to create this

const App: React.FC = () => {
  const [error, setError] = useState<string | null>(null);
  const [marketData, setMarketData] = useState<MarketData[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const loadMarketData = async () => {
      try {
        setLoading(true);
        // Replace with actual API call when ready
        const data = await fetchMarketData();
        setMarketData(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch market data');
      } finally {
        setLoading(false);
      }
    };

    loadMarketData();
  }, []);

  const handleSequenceSelect = (sequence: string[]): void => {
    try {
      if (!sequence.length) {
        throw new Error('Please select a valid sequence');
      }
      console.log('Selected sequence:', sequence);
      // Add your sequence analysis logic here
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred processing sequence');
    }
  };

  if (loading) {
    return <div className="loading">Loading market data...</div>;
  }

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
        {marketData.length > 0 ? (
          <WaterfallChart 
            data={marketData}
            selectedCohort="all"
            onSequenceSelect={handleSequenceSelect}
          />
        ) : (
          <div className="no-data">No market data available</div>
        )}
      </main>
    </div>
  );
};

export default App; 