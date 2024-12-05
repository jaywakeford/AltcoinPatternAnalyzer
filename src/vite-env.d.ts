/// <reference types="vite/client" />

declare module 'vite' {
  import type { UserConfig } from 'vite'
  export function defineConfig(config: UserConfig): UserConfig
  export type { UserConfig }
}

declare module '@vitejs/plugin-react' {
  import type { Plugin } from 'vite'
  function pluginReact(options?: any): Plugin
  export default pluginReact
}

interface ImportMetaEnv {
  readonly VITE_API_ENDPOINT: string
  readonly MODE: 'development' | 'production' | 'test'
}

interface ImportMeta {
  readonly env: ImportMetaEnv
} 