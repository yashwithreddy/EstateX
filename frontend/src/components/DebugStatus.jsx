import { useEffect, useState } from 'react';
import api from '../api/client';
import { useAuth } from '../context/AuthContext';

function DebugStatus() {
  const { user, token } = useAuth();
  const [status, setStatus] = useState('checking');

  useEffect(() => {
    let mounted = true;
    api
      .get('/', { baseURL: import.meta.env.VITE_API_ROOT || 'http://127.0.0.1:8000' })
      .then(() => mounted && setStatus('online'))
      .catch(() => mounted && setStatus('offline'));

    return () => {
      mounted = false;
    };
  }, []);

  return (
    <div className="mb-4 grid gap-2 rounded-xl border border-sky-200 bg-sky-50 p-3 text-xs text-slate-700 md:grid-cols-3">
      <p>
        API Status: <strong>{status}</strong>
      </p>
      <p>
        User Role: <strong>{user?.role || 'guest'}</strong>
      </p>
      <p>
        Token Present: <strong>{token ? 'yes' : 'no'}</strong>
      </p>
    </div>
  );
}

export default DebugStatus;
