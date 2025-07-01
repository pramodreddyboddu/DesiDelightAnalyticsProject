import { useState, useEffect, createContext, useContext } from 'react';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

  // Check authentication status on mount
  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    try {
      // Detect if we're on mobile
      const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
      
      // Use mobile-specific endpoint for mobile browsers
      const endpoint = isMobile ? '/auth/mobile-auth-check' : '/auth/me';
      
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        credentials: 'include',
        headers: {
          'User-Agent': navigator.userAgent, // Send user agent for server-side detection
        },
      });

      if (response.ok) {
        const userData = await response.json();
        setUser(userData.user);
        setIsAuthenticated(true);
        
        if (isMobile) {
          console.log('Mobile authentication successful:', userData);
        }
      } else {
        setUser(null);
        setIsAuthenticated(false);
        
        if (isMobile) {
          console.log('Mobile authentication failed, trying fallback...');
          // Try the regular endpoint as fallback
          try {
            const fallbackResponse = await fetch(`${API_BASE_URL}/auth/me`, {
              credentials: 'include',
            });
            if (fallbackResponse.ok) {
              const fallbackData = await fallbackResponse.json();
              setUser(fallbackData.user);
              setIsAuthenticated(true);
              console.log('Fallback authentication successful');
            }
          } catch (fallbackError) {
            console.error('Fallback authentication failed:', fallbackError);
          }
        }
      }
    } catch (error) {
      console.error('Auth check failed:', error);
      setUser(null);
      setIsAuthenticated(false);
    } finally {
      setLoading(false);
    }
  };

  const login = async (username, password) => {
    try {
      // Detect if we're on mobile
      const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
      
      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'User-Agent': navigator.userAgent, // Send user agent for server-side detection
        },
        credentials: 'include',
        body: JSON.stringify({ username, password }),
      });

      if (response.ok) {
        if (isMobile) {
          console.log('Mobile login successful, checking auth status...');
        }
        await checkAuthStatus();
        return { success: true };
      } else {
        const errorData = await response.json();
        return { success: false, error: errorData.error || 'Login failed' };
      }
    } catch (error) {
      console.error('Login error:', error);
      return { success: false, error: 'Network error occurred' };
    }
  };

  const logout = async () => {
    try {
      await fetch(`${API_BASE_URL}/auth/logout`, {
        method: 'POST',
        credentials: 'include',
      });
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      setUser(null);
      setIsAuthenticated(false);
    }
  };

  const value = {
    user,
    loading,
    isAuthenticated,
    login,
    logout,
    checkAuthStatus,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}; 