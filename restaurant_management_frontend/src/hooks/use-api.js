import { useState, useEffect, useCallback, useRef } from 'react';
import { useToast } from '@/components/ui/toast.jsx';

const API_BASE_URL = 'http://localhost:5000/api';

export const useApi = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const cache = useRef(new Map());
  const { success, error: showError } = useToast();

  const request = useCallback(async (endpoint, options = {}) => {
    const url = `${API_BASE_URL}${endpoint}`;
    const cacheKey = `${options.method || 'GET'}:${url}:${JSON.stringify(options.body || {})}`;
    
    // Check cache for GET requests
    if (options.method === 'GET' || !options.method) {
      const cached = cache.current.get(cacheKey);
      if (cached && Date.now() - cached.timestamp < 5 * 60 * 1000) { // 5 minutes
        return cached.data;
      }
    }

    try {
      setLoading(true);
      setError(null);

      const response = await fetch(url, {
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
        ...options,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || `HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();

      // Cache successful GET requests
      if (options.method === 'GET' || !options.method) {
        cache.current.set(cacheKey, {
          data,
          timestamp: Date.now(),
        });
      }

      return data;
    } catch (err) {
      setError(err.message);
      showError('Request Failed', err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [showError]);

  const get = useCallback((endpoint) => request(endpoint), [request]);
  
  const post = useCallback((endpoint, data) => 
    request(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    }), [request]);
  
  const put = useCallback((endpoint, data) => 
    request(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data),
    }), [request]);
  
  const del = useCallback((endpoint) => 
    request(endpoint, {
      method: 'DELETE',
    }), [request]);

  const clearCache = useCallback(() => {
    cache.current.clear();
  }, []);

  const invalidateCache = useCallback((pattern) => {
    for (const [key] of cache.current) {
      if (key.includes(pattern)) {
        cache.current.delete(key);
      }
    }
  }, []);

  return {
    loading,
    error,
    request,
    get,
    post,
    put,
    delete: del,
    clearCache,
    invalidateCache,
  };
};

export const useApiData = (endpoint, dependencies = []) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const { get, success, error: showError } = useApi();

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await get(endpoint);
      setData(result);
    } catch (err) {
      setError(err.message);
      showError('Failed to load data', err.message);
    } finally {
      setLoading(false);
    }
  }, [endpoint, get, showError]);

  const refresh = useCallback(() => {
    fetchData();
  }, [fetchData]);

  useEffect(() => {
    fetchData();
  }, [fetchData, ...dependencies]);

  return { data, loading, error, refresh };
};

export const useApiMutation = (endpoint, options = {}) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const { post, put, delete: del, invalidateCache, success } = useApi();

  const mutate = useCallback(async (data, method = 'POST') => {
    try {
      setLoading(true);
      setError(null);

      let result;
      switch (method.toUpperCase()) {
        case 'POST':
          result = await post(endpoint, data);
          break;
        case 'PUT':
          result = await put(endpoint, data);
          break;
        case 'DELETE':
          result = await del(endpoint);
          break;
        default:
          throw new Error(`Unsupported method: ${method}`);
      }

      // Invalidate related cache
      if (options.invalidateCache) {
        invalidateCache(options.invalidateCache);
      }

      // Show success message
      if (options.successMessage) {
        success('Success', options.successMessage);
      }

      return result;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [endpoint, post, put, del, invalidateCache, success, options]);

  return { mutate, loading, error };
}; 