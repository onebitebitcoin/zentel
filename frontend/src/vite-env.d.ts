/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string;
  readonly VITE_APP_NAME: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

// CSS 모듈 타입 선언
declare module '*.css' {
  const content: { [className: string]: string };
  export default content;
}
