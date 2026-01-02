import { useState, useEffect } from 'react';

interface CameraConfig {
    id: string;
    name: string;
    type: 'pc' | 'ip';
    url: string;
    active: boolean;
}

export default function Settings() {
    // --- Shared State Logic (Same as LiveMonitor) ---
    const [cameras, setCameras] = useState<CameraConfig[]>([]);

    useEffect(() => {
        const saved = localStorage.getItem('violence_monitor_cameras');
        if (saved) {
            setCameras(JSON.parse(saved));
        }
    }, []);

    const saveChanges = (newCameras: CameraConfig[]) => {
        setCameras(newCameras);
        localStorage.setItem('violence_monitor_cameras', JSON.stringify(newCameras));
    };

    const toggleCamera = async (id: string, currentState: boolean) => {
        const newState = !currentState;
        const newCameras = cameras.map(c => c.id === id ? { ...c, active: newState } : c);

        saveChanges(newCameras);

        // Sync with backend if it's the Main PC Camera
        if (id === '0') {
            try {
                await fetch(`/api/v1/cameras/0/toggle?enable=${newState}`, { method: 'POST' });
            } catch (e) { console.error("Backend sync failed"); }
        }
    };

    const removeCamera = (id: string) => {
        if (id === '0') {
            alert("Cannot remove the Main PC Camera.");
            return;
        }
        if (confirm("Are you sure you want to remove this camera?")) {
            const newCameras = cameras.filter(c => c.id !== id);
            saveChanges(newCameras);
        }
    };

    const updateName = (id: string, newName: string) => {
        const newCameras = cameras.map(c => c.id === id ? { ...c, name: newName } : c);
        saveChanges(newCameras);
    };

    return (
        <div className="flex flex-col h-full text-white p-6 gap-6 max-w-4xl mx-auto">
            <h1 className="text-3xl font-bold border-b border-slate-700 pb-4">System Settings</h1>

            <div className="bg-slate-900 rounded-xl p-6 shadow-xl border border-slate-700">
                <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                    <span>📹</span> Camera Management
                </h2>

                <div className="flex flex-col gap-3">
                    {cameras.length === 0 && (
                        <div className="text-slate-500 italic p-4 text-center">No cameras configured.</div>
                    )}

                    {cameras.map(cam => (
                        <div key={cam.id} className="flex items-center gap-4 bg-black/40 p-3 rounded-lg border border-slate-800">
                            {/* Icon */}
                            <div className="w-10 h-10 rounded-full flex items-center justify-center bg-slate-800 text-xl">
                                {cam.type === 'pc' ? '💻' : '🌐'}
                            </div>

                            {/* Details */}
                            <div className="flex-1">
                                <div className="flex items-center gap-2">
                                    <input
                                        type="text"
                                        value={cam.name}
                                        onChange={(e) => updateName(cam.id, e.target.value)}
                                        className="bg-transparent font-bold text-slate-200 border-b border-dashed border-slate-600 focus:border-purple-500 focus:outline-none px-1"
                                    />
                                    {cam.type === 'pc' && <span className="text-xs bg-blue-900 text-blue-300 px-2 py-0.5 rounded">MAIN</span>}
                                </div>
                                <div className="text-xs text-slate-500 truncate max-w-[300px]" title={cam.url}>
                                    {cam.url}
                                </div>
                            </div>

                            {/* Actions */}
                            <div className="flex items-center gap-3">
                                {/* Toggle Switch */}
                                <button
                                    onClick={() => toggleCamera(cam.id, cam.active)}
                                    className={`relative w-12 h-6 rounded-full transition-colors ${cam.active ? 'bg-green-600' : 'bg-slate-700'}`}
                                >
                                    <span className={`absolute top-1 left-1 bg-white w-4 h-4 rounded-full transition-transform ${cam.active ? 'translate-x-6' : 'translate-x-0'}`} />
                                </button>

                                {/* Delete */}
                                <button
                                    onClick={() => removeCamera(cam.id)}
                                    disabled={cam.id === '0'}
                                    className={`p-2 rounded hover:bg-red-900/50 text-slate-400 hover:text-red-400 transition-colors ${cam.id === '0' ? 'opacity-20 cursor-not-allowed' : ''}`}
                                    title="Remove Camera"
                                >
                                    🗑️
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            <div className="bg-slate-900 rounded-xl p-6 shadow-xl border border-slate-700 opacity-50 relative overflow-hidden">
                <div className="absolute inset-0 flex items-center justify-center bg-black/40 backdrop-blur-[1px] z-10">
                    <span className="font-bold tracking-widest uppercase text-slate-400 border border-slate-500 px-4 py-2 rounded">Coming Soon</span>
                </div>
                <h2 className="text-xl font-bold mb-4">📢 Notification Preferences</h2>
                <div className="space-y-4">
                    <div className="flex justify-between items-center">
                        <span>Email Alerts</span>
                        <div className="w-10 h-5 bg-slate-700 rounded-full"></div>
                    </div>
                    <div className="flex justify-between items-center">
                        <span>SMS Alerts</span>
                        <div className="w-10 h-5 bg-slate-700 rounded-full"></div>
                    </div>
                </div>
            </div>
        </div>
    );
}
