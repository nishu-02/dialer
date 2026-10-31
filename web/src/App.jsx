import { useEffect, useRef, useState } from 'react';
import { Device } from '@twilio/voice-sdk';

async function api(path, opts) {
  const res = await fetch(`/api${path}`, {
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    ...opts,
  });
  if (!res.ok) throw new Error((await res.json().catch(() => ({}))).error || res.statusText);
  return res.status === 204 ? null : res.json();
}

function formatDuration(seconds) {
  if (seconds == null) return '—';
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${String(s).padStart(2, '0')}`;
}

function timeAgo(iso) {
  const diff = (Date.now() - new Date(iso + 'Z').getTime()) / 1000;
  if (diff < 60) return 'just now';
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return new Date(iso + 'Z').toLocaleDateString();
}

function Login({ onLogin }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  async function submit(e) {
    e.preventDefault();
    try {
      await api('/login', { method: 'POST', body: JSON.stringify({ email, password }) });
      onLogin();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="login-screen">
      <form onSubmit={submit} className="login-card">
        <h1>Dialer</h1>
        <input placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} autoFocus />
        <input
          placeholder="Password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        {error && <p className="error">{error}</p>}
        <button type="submit">Log in</button>
      </form>
    </div>
  );
}

function StatusBadge({ status }) {
  const tone = status === 'completed' ? 'ok' : status === 'failed' || status === 'no-answer' ? 'bad' : 'pending';
  return <span className={`badge badge-${tone}`}>{status}</span>;
}

function Dialer() {
  const [to, setTo] = useState('');
  const [calls, setCalls] = useState([]);
  const [error, setError] = useState('');
  const [deviceReady, setDeviceReady] = useState(false);
  const [callState, setCallState] = useState('idle'); // idle | connecting | in-call
  const [elapsed, setElapsed] = useState(0);
  const deviceRef = useRef(null);
  const activeCallRef = useRef(null);
  const timerRef = useRef(null);

  async function refresh() {
    setCalls(await api('/calls'));
  }

  // Twilio's status webhook can land a moment after hangup, so a single refresh
  // right away often still shows the stale row — re-poll a couple more times.
  function refreshSoon() {
    refresh();
    setTimeout(refresh, 1500);
    setTimeout(refresh, 4000);
  }

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, 5000);
    return () => clearInterval(id);
  }, []);

  useEffect(() => {
    let device;
    (async () => {
      try {
        const { token } = await api('/voice-token');
        device = new Device(token, { codecPreferences: ['opus', 'pcmu'] });
        device.on('registered', () => setDeviceReady(true));
        device.on('error', (e) => setError(e.message));
        await device.register();
        deviceRef.current = device;
      } catch (err) {
        setError(err.message);
      }
    })();
    return () => device?.destroy();
  }, []);

  async function call(e) {
    e.preventDefault();
    setError('');
    if (!deviceRef.current || !to.trim()) return;
    try {
      setCallState('connecting');
      const conn = await deviceRef.current.connect({ params: { To: to.trim() } });
      activeCallRef.current = conn;
      conn.on('accept', () => {
        setCallState('in-call');
        setElapsed(0);
        timerRef.current = setInterval(() => setElapsed((e) => e + 1), 1000);
      });
      conn.on('disconnect', () => {
        clearInterval(timerRef.current);
        setCallState('idle');
        setTo('');
        refreshSoon();
      });
      conn.on('error', (e) => {
        clearInterval(timerRef.current);
        setError(e.message);
        setCallState('idle');
      });
    } catch (err) {
      setError(err.message);
      setCallState('idle');
    }
  }

  function hangUp() {
    activeCallRef.current?.disconnect();
  }

  return (
    <div className="page">
      <div className="dial-card">
        <p className="connection-status">{deviceReady ? 'Ready' : 'Connecting…'}</p>

        <form onSubmit={call} className="dial-form">
          <input
            className="dial-input"
            placeholder="Enter number"
            value={to}
            onChange={(e) => setTo(e.target.value)}
            disabled={!deviceReady || callState !== 'idle'}
            autoFocus
          />
          {callState === 'idle' ? (
            <button type="submit" className="call-btn" disabled={!deviceReady || !to.trim()}>
              Call
            </button>
          ) : (
            <button type="button" className="hangup-btn" onClick={hangUp}>
              {callState === 'connecting' ? 'Connecting…' : `End · ${formatDuration(elapsed)}`}
            </button>
          )}
        </form>
        {error && <p className="error">{error}</p>}
      </div>

      <div className="history">
        <h2>Recent calls</h2>
        {calls.length === 0 && <p className="empty">No calls yet</p>}
        <ul>
          {calls.map((c) => (
            <li key={c.sid} className="call-row">
              <div className="call-main">
                <span className="call-number">{c.to_number}</span>
                <span className="call-region">{c.region === 'national' ? 'India' : 'International'}</span>
              </div>
              <div className="call-meta">
                <StatusBadge status={c.status} />
                <span className="call-duration">{formatDuration(c.duration)}</span>
                <span className="call-time">{timeAgo(c.created_at)}</span>
                {c.recording_sid && (
                  <audio controls preload="none" src={`/api/recordings/${c.recording_sid}`} />
                )}
              </div>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

export default function App() {
  const [loggedIn, setLoggedIn] = useState(null);

  useEffect(() => {
    api('/me').then(() => setLoggedIn(true)).catch(() => setLoggedIn(false));
  }, []);

  if (loggedIn === null) return null;
  return loggedIn ? <Dialer /> : <Login onLogin={() => setLoggedIn(true)} />;
}
