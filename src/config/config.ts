interface Config {
  port: number;
  apiEndpoint: string;
  environment: 'development' | 'production' | 'test';
}

const config: Config = {
  port: 3002,
  apiEndpoint: import.meta.env.VITE_API_ENDPOINT || 'https://api.example.com/v1',
  environment: (import.meta.env.MODE as Config['environment']) || 'development'
};

export default config; 