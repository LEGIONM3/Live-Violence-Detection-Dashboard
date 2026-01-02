import { useState, useEffect } from 'react'
import { Switch } from '@headlessui/react'
import { TrashIcon } from '@heroicons/react/24/outline'

export default function Security() {
    const [cameras, setCameras] = useState<any[]>([])
    const [loading, setLoading] = useState(false)

    useEffect(() => {
        fetchCameras()
    }, [])

    const fetchCameras = async () => {
        try {
            const res = await fetch('/api/v1/cameras/')
            if (res.ok) {
                const data = await res.json()
                setCameras(data)
            }
        } catch (e) {
            console.error("Failed to fetch cameras")
        }
    }

    const toggleCamera = async (id: number, currentState: boolean) => {
        try {
            const res = await fetch(`/api/v1/cameras/${id}/toggle?enable=${!currentState}`, {
                method: 'POST'
            })
            if (res.ok) {
                fetchCameras() // Refresh
            }
        } catch (e) {
            console.error("Failed to toggle camera")
        }
    }

    const clearHistory = async () => {
        setLoading(true)
        try {
            await fetch('/api/v1/history/clear', { method: 'DELETE' })
            alert("History cleared successfully")
        } catch (e) {
            alert("Failed to clear history")
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="max-w-4xl mx-auto space-y-8">
            <h1 className="text-2xl font-bold text-white">Security Module</h1>

            {/* Camera Management Section */}
            <div className="bg-slate-800 rounded-lg shadow-lg p-6">
                <h2 className="text-xl font-semibold text-white mb-4">Camera Management</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {cameras.map((cam) => (
                        <div key={cam.id} className="flex items-center justify-between bg-slate-700/50 p-4 rounded-lg">
                            <div>
                                <h3 className="text-white font-medium">{cam.name}</h3>
                                <p className="text-sm text-slate-400">ID: {cam.id} - {cam.type}</p>
                            </div>
                            <Switch
                                checked={cam.active}
                                onChange={() => toggleCamera(cam.id, cam.active)}
                                className={`${cam.active ? 'bg-indigo-600' : 'bg-slate-600'
                                    } relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 focus:ring-offset-slate-900`}
                            >
                                <span className="sr-only">Enable camera</span>
                                <span
                                    className={`${cam.active ? 'translate-x-6' : 'translate-x-1'
                                        } inline-block h-4 w-4 transform rounded-full bg-white transition-transform`}
                                />
                            </Switch>
                        </div>
                    ))}
                </div>
            </div>

            {/* History Management Section */}
            <div className="bg-slate-800 rounded-lg shadow-lg p-6">
                <h2 className="text-xl font-semibold text-white mb-4">History Management</h2>
                <div className="flex items-center justify-between">
                    <div>
                        <p className="text-slate-300">Clear all detection history from the database.</p>
                        <p className="text-xs text-slate-500 mt-1">This action cannot be undone.</p>
                    </div>
                    <button
                        onClick={clearHistory}
                        disabled={loading}
                        className="flex items-center rounded-md bg-red-600 px-4 py-2 text-sm font-semibold text-white hover:bg-red-500"
                    >
                        <TrashIcon className="h-5 w-5 mr-2" />
                        Clear History
                    </button>
                </div>
            </div>

            {/* System Info Section */}
            <div className="bg-slate-800 rounded-lg shadow-lg p-6">
                <h2 className="text-xl font-semibold text-white mb-2">System Information</h2>
                <div className="bg-slate-900 rounded p-4 border border-slate-700">
                    <p className="text-indigo-400 font-mono">Version v1 Prototype</p>
                </div>
            </div>
        </div>
    )
}
