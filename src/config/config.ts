interface Config {
  apiEndpoint: string;
  environment: 'development' | 'production' | 'test';
}

const config: Config = {
  apiEndpoint: import.meta.env.VITE_API_ENDPOINT || 'https://api.binance.com/api/v3',
  environment: (import.meta.env.MODE as Config['environment']) || 'development'
};

export default config; 