import { useEffect, useRef, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';

const SESSION_TIMEOUT = 15 * 60 * 1000; // 15 minutes in ms
const WARNING_BEFORE = 2 * 60 * 1000; // Show warning 2 minutes before

const useSessionTimeout = () => {
  const { isAuthenticated, logout } = useAuth();
  const timeoutRef = useRef(null);
  const warningRef = useRef(null);

  const resetTimer = useCallback(() => {
    if (!isAuthenticated) return;

    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    if (warningRef.current) clearTimeout(warningRef.current);

    warningRef.current = setTimeout(() => {
      // Could show a modal here
      console.warn('Session will expire in 2 minutes due to inactivity');
    }, SESSION_TIMEOUT - WARNING_BEFORE);

    timeoutRef.current = setTimeout(() => {
      logout();
      window.location.href = '/login?reason=timeout';
    }, SESSION_TIMEOUT);
  }, [isAuthenticated, logout]);

  useEffect(() => {
    if (!isAuthenticated) return;

    const events = ['mousedown', 'keydown', 'scroll', 'touchstart', 'click'];
    events.forEach(event => document.addEventListener(event, resetTimer));
    resetTimer();

    return () => {
      events.forEach(event => document.removeEventListener(event, resetTimer));
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
      if (warningRef.current) clearTimeout(warningRef.current);
    };
  }, [isAuthenticated, resetTimer]);
};

export default useSessionTimeout;
