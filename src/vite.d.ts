declare module 'vite' {
  interface UserConfig {
    plugins?: any[]
    resolve?: {
      alias?: Record<string, string>
    }
    server?: {
      port?: number
      host?: boolean | string
      strictPort?: boolean
      open?: boolean | string
      proxy?: Record<string, any>
      cors?: boolean
      headers?: Record<string, string>
    }
  }

  export function defineConfig(config: UserConfig): UserConfig
}

declare module '@vitejs/plugin-react' {
  import type { Plugin } from 'vite'
  export default function(options?: any): Plugin
}

declare module 'vite/client' {
  interface ImportMetaEnv {
    readonly VITE_API_ENDPOINT: string
    readonly MODE: 'development' | 'production' | 'test'
  }

  interface ImportMeta {
    readonly env: ImportMetaEnv
  }
} 