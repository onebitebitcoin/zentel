import '@testing-library/jest-dom';

// Mock import.meta.env
Object.defineProperty(import.meta, 'env', {
  value: {
    DEV: true,
    PROD: false,
    MODE: 'test',
    VITE_API_URL: '/api/v1',
  },
});
