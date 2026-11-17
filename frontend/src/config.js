import { Platform } from 'react-native';

/**
 * Resolves API URL based on runtime environment:
 * 1. Explicit EXPO_PUBLIC_API_URL env variable if provided.
 * 2. Android emulator host (10.0.2.2:8000).
 * 3. Localhost for Web / iOS simulator (localhost:8000).
 */
const resolveApiBaseUrl = () => {
  if (process.env.EXPO_PUBLIC_API_URL) {
    return process.env.EXPO_PUBLIC_API_URL.replace(/\/+$/, '');
  }
  if (Platform.OS === 'android') {
    return 'http://10.0.2.2:8000';
  }
  return 'http://localhost:8000';
};

export const API_BASE_URL = resolveApiBaseUrl();
