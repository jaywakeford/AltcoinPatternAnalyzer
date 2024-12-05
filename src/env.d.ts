/// <reference types="vite/client" />
/// <reference types="react" />
/// <reference types="react-dom" />

declare module '*.svg' {
  import * as React from 'react';
  export const ReactComponent: React.FunctionComponent<React.SVGProps<SVGSVGElement>>;
  const src: string;
  export default src;
}

interface ImportMetaEnv {
  readonly VITE_API_ENDPOINT: string;
  readonly MODE: 'development' | 'production' | 'test';
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

declare module 'react' {
  export interface JSX {
    IntrinsicElements: {
      [elemName: string]: any;
    };
  }
  
  export type FC<P = {}> = React.FunctionComponent<P>;
  export const useState: typeof React.useState;
  export const useEffect: typeof React.useEffect;
  export const useRef: typeof React.useRef;
  export const StrictMode: typeof React.StrictMode;
}

declare module 'react/jsx-runtime' {
  export const jsx: any;
  export const jsxs: any;
  export const Fragment: any;
} 