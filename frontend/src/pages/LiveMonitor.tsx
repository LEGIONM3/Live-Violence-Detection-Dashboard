
import { useState, useEffect, useRef } from 'react';

// Interfaces for our data
interface Detection {
    label: string;
    confidence: number;
}

interface InferenceResult {
    violence_detected: boolean;
    confidence: number;
    detections: Detection[];
}

interface CameraConfig {
    id: string;
    name: string;
    type: 'pc' | 'ip';
    url: string;
    active: boolean;
}

// Fixed PC Camera Config
const PC_CAM_DEFAULT: CameraConfig = {
    id: '0',
    name: 'Main PC Camera',
    type: 'pc',
    url: '/api/v1/cameras/0/feed',
    active: true
};

export default function LiveMonitor() {
    // --- State ---
    // Camera List (Persisted in LocalStorage)
    const [cameras, setCameras] = useState<CameraConfig[]>(() => {
        const saved = localStorage.getItem('violence_monitor_cameras');
        if (saved) {
            const parsed = JSON.parse(saved);
            // Ensure PC cam is always present and first
            if (!parsed.find((c: CameraConfig) => c.id === '0')) {
                return [PC_CAM_DEFAULT, ...parsed];
            }
            return parsed;
        }
        return [PC_CAM_DEFAULT];
    });

    // New Camera Input
    const [newCamUrl, setNewCamUrl] = useState('');

    // Backend WS State
    const wsRef = useRef<WebSocket | null>(null);

    // Alert logic
    const [alertState, setAlertState] = useState<'secure' | 'suspicious' | 'confirmed'>('secure');
    const [latestReport, setLatestReport] = useState<string>("Waiting for analysis...");
    const [suspicionMsg, setSuspicionMsg] = useState("");

    // --- Effects ---

    // 1. Persist Cameras
    useEffect(() => {
        localStorage.setItem('violence_monitor_cameras', JSON.stringify(cameras));
    }, [cameras]);

    // 2. Sync PC Camera State with Backend (Initial)
    useEffect(() => {
        fetch('/api/v1/cameras/')
            .then(res => res.json())
            .then(data => {
                const pc = data.find((c: any) => c.id === "0");
                if (pc) {
                    // Update valid backend state matching our local config
                    setCameras(prev => prev.map(c =>
                        c.id === '0' ? { ...c, active: pc.active } : c
                    ));
                }
            })
            .catch(err => console.error("Failed to sync backend camera state", err));
    }, []);

    // 3. WS Connection
    useEffect(() => {
        const host = window.location.host;
        // However, since we proxy /ws -> target, we usually connect to current host/api...
        // But vite config proxies /ws to ws://127.0.0.1:8000
        // So we should connect to `ws://${window.location.host}/ws` or similar if path rewriting.
        // The backend route is /api/v1/cameras/ws.
        // Let's rely on the proxy path.
        const wsUrl = `ws://${host}/api/v1/cameras/ws`; // Proxy handles target

        const connect = () => {
            const ws = new WebSocket(wsUrl);
            ws.onopen = () => { };
            ws.onclose = () => {
                setTimeout(connect, 3000);
            };
            ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);

                    if (data.type === "inference_status") {
                        setLatestReport(data.message || "Monitoring...");
                        if (data.status === "suspicious") {
                            setAlertState(prev => prev === 'confirmed' ? 'confirmed' : 'suspicious');
                            setSuspicionMsg(data.message || "Activity Detected");
                        } else if (data.status === "secure") {
                            setAlertState(prev => prev === 'confirmed' ? 'confirmed' : 'secure');
                        }
                    }

                    if (data.type === "alert_confirmed") {
                        setAlertState('confirmed');
                        setLatestReport(data.text + ` [Latency: ${data.latency}]`);
                    }

                    if (data.type === "analysis_report") setLatestReport(data.text);

                } catch (e) { }
            };
            wsRef.current = ws;
        };
        connect();
        return () => wsRef.current?.close();
    }, []);

    // --- Actions ---

    const addCamera = () => {
        if (!newCamUrl.trim()) return;
        const newCam: CameraConfig = {
            id: Date.now().toString(),
            name: `IP Camera ${cameras.length}`,
            type: 'ip',
            url: newCamUrl,
            active: true
        };
        setCameras([...cameras, newCam]);
        setNewCamUrl('');
    };

    const toggleCamera = async (id: string, currentState: boolean) => {
        const newState = !currentState;

        // 1. Update UI immediately
        setCameras(prev => prev.map(c => c.id === id ? { ...c, active: newState } : c));

        // 2. If PC Camera, sync with Backend
        if (id === '0') {
            try {
                await fetch(`/api/v1/cameras/0/toggle?enable=${newState}`, { method: 'POST' });
            } catch (e) {
                console.error("Backend toggle failed", e);
                // Revert on fail?
            }
        }
    };

    const removeCamera = (id: string) => {
        if (id === '0') return; // Cannot remove main camera
        setCameras(prev => prev.filter(c => c.id !== id));
    };

    return (
        <div className="flex flex-col h-full text-white p-6 gap-6">
            <h1 className="text-3xl font-bold">Dual-Source Surveillance</h1>

            {/* Control Bar */}
            <div className="flex gap-4 p-4 bg-slate-800 rounded-lg items-center flex-wrap">
                <div className="flex items-center gap-4 flex-1 min-w-[300px]">
                    <span className="font-bold text-slate-300">Add Camera Source:</span>
                    <div className="flex flex-1 gap-2">
                        <input
                            type="text"
                            value={newCamUrl}
                            onChange={(e) => setNewCamUrl(e.target.value)}
                            placeholder="Enter IP Camera URL (e.g., http://192.168.1.5:8080/video)"
                            className="bg-slate-700 border border-slate-600 rounded px-3 py-2 text-sm flex-1 focus:outline-none focus:border-purple-500 transition-colors"
                        />
                        <button
                            onClick={addCamera}
                            className="bg-purple-600 px-4 py-2 rounded text-sm font-bold hover:bg-purple-500 transition-colors flex items-center gap-2"
                        >
                            <span>+</span> Add
                        </button>
                    </div>
                </div>

                {/* Active Camera Toggles (Mini Quick View) */}
                <div className="flex gap-2 items-center border-l border-slate-600 pl-4">
                    <span className="text-xs text-slate-500 uppercase font-bold">Quick Toggles:</span>
                    {cameras.map(cam => (
                        <button
                            key={cam.id}
                            onClick={() => toggleCamera(cam.id, cam.active)}
                            className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold transition-all ${cam.active ? 'bg-green-600 shadow-[0_0_10px_rgba(34,197,94,0.4)]' : 'bg-red-900/50 text-red-400'}`}
                            title={`Toggle ${cam.name}`}
                        >
                            {cam.id === '0' ? 'PC' : cam.id.slice(-1)}
                        </button>
                    ))}
                </div>
            </div>

            {/* Feeds Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 flex-1 min-h-[400px]">
                {cameras.map((cam, idx) => (
                    <div key={cam.id} className={`relative rounded-xl overflow-hidden border-2 flex flex-col bg-black transition-all ${cam.active ? 'border-slate-700 shadow-lg' : 'border-red-900/20 opacity-70 grayscale'
                        }`}>
                        {/* Feed Header */}
                        <div className="absolute top-0 left-0 right-0 p-2 bg-gradient-to-b from-black/80 to-transparent z-10 flex justify-between items-start">
                            <div className="bg-black/50 backdrop-blur-sm px-2 py-1 rounded text-xs font-mono font-bold border border-white/10">
                                {cam.name}
                            </div>
                            <div className="flex gap-2">
                                <button
                                    onClick={() => toggleCamera(cam.id, cam.active)}
                                    className={`px-2 py-1 rounded text-xs font-bold border ${cam.active ? 'bg-green-500/20 border-green-500 text-green-400' : 'bg-red-500/20 border-red-500 text-red-400'}`}
                                >
                                    {cam.active ? 'LIVE' : 'OFF'}
                                </button>
                                {cam.id !== '0' && (
                                    <button
                                        onClick={() => removeCamera(cam.id)}
                                        className="w-6 h-6 rounded bg-black/50 text-slate-400 hover:text-red-400 flex items-center justify-center"
                                    >
                                        ×
                                    </button>
                                )}
                            </div>
                        </div>

                        {/* Video Area */}
                        <div className="flex-1 relative flex items-center justify-center bg-zinc-900">
                            {cam.active ? (
                                cam.type === 'pc' ? (
                                    <img src={cam.url} className="w-full h-full object-contain" alt="Main Feed" />
                                ) : (
                                    <img
                                        src={cam.url}
                                        className="w-full h-full object-contain"
                                        alt="IP Feed"
                                        onError={(e) => {
                                            e.currentTarget.style.display = 'none';
                                            e.currentTarget.parentElement?.classList.add('feed-error');
                                        }}
                                    />
                                )
                            ) : (
                                <div className="flex flex-col items-center justify-center text-slate-600 gap-2">
                                    <div className="text-4xl">🚫</div>
                                    <span className="font-mono text-xs">FEED TERMINATED</span>
                                </div>
                            )}

                            {/* Error State Fallback (Pseudo-element via JS logic above usually, but helpful text here) */}
                            {cam.active && cam.type === 'ip' && (
                                <div className="hidden feed-error-msg absolute inset-0 flex-col items-center justify-center bg-zinc-900 text-slate-500">
                                    <span>Signal Lost</span>
                                    <span className="text-xs">{cam.url}</span>
                                </div>
                            )}
                        </div>
                    </div>
                ))}
            </div>

            {/* Real-Time Analysis Panel (Context Aware - Focused on Main Camera usually) */}
            <div className="bg-slate-900 rounded-xl border border-slate-700 p-6 shadow-xl">
                <div className="flex items-center justify-between mb-4">
                    <h2 className="text-xl font-bold flex items-center gap-2">
                        <span className="w-1 h-6 bg-purple-500 rounded-full"></span>
                        Real-Time Analysis Stream (Main Channel)
                    </h2>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Alert Status Card */}
                    <div className={`p-6 rounded-lg border-2 flex flex-col items-center justify-center text-center transition-all duration-300 ${alertState === 'confirmed'
                        ? 'bg-red-950/80 border-red-500 text-white animate-pulse shadow-[0_0_30px_rgba(239,68,68,0.4)]'
                        : alertState === 'suspicious'
                            ? 'bg-yellow-900/50 border-yellow-500 text-yellow-100 shadow-[0_0_20px_rgba(234,179,8,0.2)]'
                            : 'bg-slate-800/50 border-slate-700/50 text-slate-400'
                        }`}>
                        {alertState === 'confirmed' ? (
                            <>
                                <div className="text-6xl mb-4">⚠️</div>
                                <h3 className="text-3xl font-extrabold uppercase tracking-wider mb-2">VIOLENCE DETECTED</h3>
                                <p className="text-red-200 mb-6 font-mono text-sm">{latestReport}</p>
                                <button
                                    onClick={() => setAlertState('secure')}
                                    className="px-6 py-2 bg-white text-red-900 font-bold rounded hover:bg-red-100 transition-colors pointer-events-auto"
                                >
                                    ACKNOWLEDGE
                                </button>
                            </>
                        ) : (
                            <>
                                <div className={`text-4xl mb-2 ${alertState === 'suspicious' ? 'text-yellow-400' : 'text-green-500'}`}>
                                    {alertState === 'suspicious' ? '👁️' : '🛡️'}
                                </div>
                                <h3 className={`text-lg font-semibold uppercase tracking-wider ${alertState === 'suspicious' ? 'text-yellow-400' : 'text-green-400'}`}>
                                    {alertState === 'suspicious' ? 'Analyzing Activity' : 'Secure Environment'}
                                </h3>
                                <p className="text-xs text-slate-500 mt-2">
                                    {alertState === 'suspicious' ? suspicionMsg : 'Monitoring Active'}
                                </p>
                            </>
                        )}
                    </div>

                    {/* Analysis Report Card */}
                    <div className="p-4 rounded-lg bg-black/40 border border-slate-800 flex flex-col">
                        <h3 className="text-xs uppercase tracking-widest text-slate-500 mb-2 border-b border-slate-800 pb-2">Live Classification Reports</h3>
                        <div className="flex-1 font-mono text-sm leading-relaxed text-blue-200 overflow-y-auto max-h-[120px]">
                            <span className={alertState === 'confirmed' ? 'text-red-400 font-bold' : 'text-slate-400'}>
                                {latestReport}
                            </span>
                        </div>
                        {latestReport !== "Waiting for analysis..." && (
                            <div className="mt-2 text-xs text-right text-slate-500">
                                Model: SlowFast (Deep)
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    )
}
