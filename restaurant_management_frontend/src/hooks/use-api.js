import { useState, useEffect, useCallback, useRef } from 'react';
import { useToast } from '@/components/ui/toast.jsx';

const API_BASE_URL = 'http://localhost:5000/api';

export const useApi = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const cache = useRef(new Map());
  const { success, error: showError } = useToast();

  const request = useCallback(async (url, options = {}) => {
    // If url doesn't start with http, prepend the base URL
    const fullUrl = url.startsWith('http') ? url : `${API_BASE_URL}${url}`;
    const cacheKey = `${options.method || 'GET'}:${fullUrl}:${JSON.stringify(options.body || {})}`;
    
    // Check cache for GET requests (but not for dashboard endpoints)
    if ((options.method === 'GET' || !options.method) && !fullUrl.includes('/dashboard/')) {
      const cached = cache.current.get(cacheKey);
      if (cached && Date.now() - cached.timestamp < 5 * 60 * 1000) { // 5 minutes
        return cached.data;
      }
    }

    try {
      setLoading(true);
      setError(null);

      const response = await fetch(fullUrl, {
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

      // Cache successful GET requests (but not for dashboard endpoints)
      if ((options.method === 'GET' || !options.method) && !fullUrl.includes('/dashboard/')) {
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

  const get = useCallback((url) => request(url), [request]);
  
  const post = useCallback((url, data) => 
    request(url, {
      method: 'POST',
      body: JSON.stringify(data),
    }), [request]);
  
  const put = useCallback((url, data) => 
    request(url, {
      method: 'PUT',
      body: JSON.stringify(data),
    }), [request]);
  
  const del = useCallback((url) => 
    request(url, {
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

export const useApiData = (url, dependencies = null, options = {}) => {
  const { showToast = true, initialData = null } = options;
  const [data, setData] = useState(initialData);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const { get } = useApi();
  const { success, error: showError } = useToast();

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const params = new URLSearchParams();
      
      if (dependencies && typeof dependencies === 'object') {
        Object.entries(dependencies).forEach(([key, value]) => {
          if (value !== null && value !== undefined && value !== 'all') {
            params.append(key, value);
          }
        });
      }
      
      const fullUrl = params.toString() ? `${url}?${params.toString()}` : url;
      
      const result = await get(fullUrl);
      setData(result);
    } catch (err) {
      setError(err);
      if (showToast) {
        showError('Failed to load data', err.error || 'An unexpected error occurred');
      }
    } finally {
      setLoading(false);
    }
  }, [url, get, showError, ...(Array.isArray(dependencies) ? dependencies : (dependencies ? Object.values(dependencies) : []))]);

  // Call fetchData when component mounts or dependencies change
  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const refresh = useCallback(() => {
    fetchData();
  }, [fetchData]);

  return { data, loading, error, refresh };
};

export const useApiMutation = (endpoint, options = {}) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const { request, invalidateCache } = useApi();
  const { success: showSuccess, error: showError } = useToast();

  const mutate = useCallback(async (variables) => {
    try {
      setLoading(true);
      setError(null);

      // If endpoint is a function, call it with variables to get the dynamic URL
      const url = typeof endpoint === 'function' ? endpoint(variables) : endpoint;
      
      const method = options.method || 'POST';
      const body = options.method !== 'GET' ? JSON.stringify(variables) : undefined;

      const result = await request(url, {
        method: method,
        body: body,
      });

      // Invalidate related cache
      if (options.invalidateCache) {
        invalidateCache(options.invalidateCache);
      }

      // Show success message
      if (options.onSuccess) {
          options.onSuccess(result, variables);
      } else if (options.successMessage) {
        showSuccess('Success', options.successMessage);
      }

      return result;
    } catch (err) {
        if(options.onError) {
            options.onError(err, variables);
        } else {
            setError(err.message);
            showError('Mutation Failed', err.message);
        }
      throw err;
    } finally {
      setLoading(false);
    }
  }, [endpoint, options, request, invalidateCache, showSuccess, showError]);

  return { mutate, loading, error };
}; 