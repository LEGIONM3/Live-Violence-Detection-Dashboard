
import { useState, useEffect } from 'react'
import { TrashIcon } from '@heroicons/react/24/outline'

export default function History() {
    const [dbHistory, setDbHistory] = useState([])
    const [loading, setLoading] = useState(false)

    useEffect(() => {
        fetchHistory()
        const interval = setInterval(fetchHistory, 5000)
        return () => clearInterval(interval)
    }, [])

    const fetchHistory = async () => {
        try {
            const res = await fetch('/api/v1/history/')
            if (res.ok) {
                const data = await res.json()
                setDbHistory(data)
            }
        } catch (err) {
            console.error("Failed to fetch history", err)
        }
    }

    const clearDbHistory = async () => {
        setLoading(true)
        try {
            await fetch('/api/v1/history/clear', { method: 'DELETE' })
            setDbHistory([])
        } catch (err) {
            console.error("Failed to clear history", err)
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <h2 className="text-3xl font-bold text-white">Incident History</h2>
                <button
                    onClick={clearDbHistory}
                    disabled={loading}
                    className="flex items-center bg-red-600 px-3 py-2 rounded text-sm font-semibold text-white hover:bg-red-500"
                >
                    <TrashIcon className="h-5 w-5 mr-2" />
                    Clear History
                </button>
            </div>

            <div className="bg-slate-800 rounded-lg shadow overflow-hidden">
                <table className="min-w-full divide-y divide-slate-700">
                    <thead className="bg-slate-900">
                        <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">Time</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">Source</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">Analysis (Local AI)</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">Evidence</th>
                        </tr>
                    </thead>
                    <tbody className="bg-slate-800 divide-y divide-slate-700">
                        {dbHistory.map((row: any, idx) => (
                            <tr key={idx}>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-300">
                                    {new Date(row.timestamp + 'Z').toLocaleString()}
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-300">
                                    {row.camera_id}
                                </td>
                                <td className="px-6 py-4 text-sm text-slate-300 max-w-md">
                                    <div className="font-semibold text-blue-300 mb-1">REAL-TIME CLASSIFICATION:</div>
                                    {row.details && <p className="text-gray-400 mb-1">{row.details}</p>}
                                    <p className="line-clamp-3">{row.analysis_result || "Pending Analysis..."}</p>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-300">
                                    {row.evidence_path ? (
                                        <span className="text-green-400 font-mono text-xs border border-green-900 bg-green-900/20 px-2 py-1 rounded">
                                            {row.evidence_path.split('\\').pop()}
                                        </span>
                                    ) : <span className="text-slate-500">-</span>}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
                {dbHistory.length === 0 && <div className="p-8 text-center text-slate-400">No violent incidents recorded.</div>}
            </div>
        </div>
    )
}
