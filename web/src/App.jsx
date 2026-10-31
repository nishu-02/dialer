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
    <form onSubmit={submit} className="login">
      <h1>Dialer login</h1>
      <input placeholder="email" value={email} onChange={(e) => setEmail(e.target.value)} />
      <input
        placeholder="password"
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
      />
      {error && <p className="error">{error}</p>}
      <button type="submit">Log in</button>
    </form>
  );
}

function Dialer() {
  const [to, setTo] = useState('');
  const [calls, setCalls] = useState([]);
  const [error, setError] = useState('');
  const [deviceReady, setDeviceReady] = useState(false);
  const [callState, setCallState] = useState('idle'); // idle | connecting | in-call
  const deviceRef = useRef(null);
  const activeCallRef = useRef(null);

  async function refresh() {
    setCalls(await api('/calls'));
  }

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, 3000); // poll; websockets are overkill for v1
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
    if (!deviceRef.current) return;
    try {
      setCallState('connecting');
      const conn = await deviceRef.current.connect({ params: { To: to } });
      activeCallRef.current = conn;
      conn.on('accept', () => setCallState('in-call'));
      conn.on('disconnect', () => {
        setCallState('idle');
        refresh();
      });
      conn.on('error', (e) => {
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
    <div className="dialer">
      <p className="status">{deviceReady ? 'Ready to call' : 'Connecting to Twilio…'}</p>
      <form onSubmit={call}>
        <input
          placeholder="+91 9876543210"
          value={to}
          onChange={(e) => setTo(e.target.value)}
          disabled={!deviceReady || callState !== 'idle'}
        />
        {callState === 'idle' ? (
          <button type="submit" disabled={!deviceReady}>
            Call
          </button>
        ) : (
          <button type="button" onClick={hangUp}>
            Hang up ({callState})
          </button>
        )}
      </form>
      {error && <p className="error">{error}</p>}

      <table>
        <thead>
          <tr>
            <th>To</th>
            <th>Region</th>
            <th>Status</th>
            <th>Duration</th>
            <th>Recording</th>
          </tr>
        </thead>
        <tbody>
          {calls.map((c) => (
            <tr key={c.sid}>
              <td>{c.to_number}</td>
              <td>{c.region}</td>
              <td>{c.status}</td>
              <td>{c.duration ?? '-'}</td>
              <td>
                {c.recording_sid ? (
                  <audio controls src={`/api/recordings/${c.recording_sid}`} />
                ) : (
                  '-'
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
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
