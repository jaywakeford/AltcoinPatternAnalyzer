/// <reference types="vite/client" />

declare module 'vite' {
  export interface UserConfig {
    // Add Vite config types here
  }

  export function defineConfig(config: UserConfig): UserConfig
}

declare module '@vitejs/plugin-react' {
  import type { Plugin } from 'vite'
  export default function react(options?: any): Plugin
}

interface ImportMetaEnv {
  readonly VITE_API_ENDPOINT: string
  readonly MODE: 'development' | 'production' | 'test'
}

interface ImportMeta {
  readonly env: ImportMetaEnv
} 