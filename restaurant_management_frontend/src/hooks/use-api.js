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

export const useApiData = (endpoint, dependencies = []) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const { get } = useApi();
  const { success, error: showError } = useToast();

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Build query parameters
      const params = new URLSearchParams();
      
      if (Array.isArray(dependencies)) {
        // Handle array format (legacy support)
        if (dependencies[0] && dependencies[0].from) {
          params.append('start_date', dependencies[0].from.toISOString());
        }
        if (dependencies[0] && dependencies[0].to) {
          params.append('end_date', dependencies[0].to.toISOString());
        }
        
        if (dependencies[1] && dependencies[1] !== 'all') {
          params.append('category', dependencies[1]);
        }
        
        if (dependencies[2] && dependencies[2] !== 'all') {
          params.append('chef_id', dependencies[2]);
        }
      } else if (typeof dependencies === 'object') {
        // Handle object format (new format)
        Object.entries(dependencies).forEach(([key, value]) => {
          if (value !== null && value !== undefined && value !== 'all') {
            params.append(key, value);
          }
        });
      }
      
      // Build the full URL with query parameters
      const url = params.toString() ? `${endpoint}?${params.toString()}` : endpoint;
      
      const result = await get(url);
      setData(result);
    } catch (err) {
      setError(err.message);
      showError('Failed to load data', err.message);
    } finally {
      setLoading(false);
    }
  }, [endpoint, get, showError, ...(Array.isArray(dependencies) ? dependencies : Object.values(dependencies))]);

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
  const { post, put, delete: del, invalidateCache } = useApi();
  const { success } = useToast();

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