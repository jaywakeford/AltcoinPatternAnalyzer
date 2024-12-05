/// <reference path="./src/vite.d.ts" />
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': '/src',
    },
  },
  server: {
    port: 4000,
    host: '::',
    cors: true,
  },
}); 