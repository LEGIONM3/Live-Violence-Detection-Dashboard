import { useState, useRef } from 'react'
import { CloudArrowUpIcon, DocumentMagnifyingGlassIcon } from '@heroicons/react/24/outline'

export default function Authenticator() {
    const [file, setFile] = useState<File | null>(null)
    const [result, setResult] = useState<any>(null)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const fileInputRef = useRef<HTMLInputElement>(null)

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            setFile(e.target.files[0])
            setResult(null)
            setError(null)
        }
    }

    const handleClassify = async () => {
        if (!file) return

        setLoading(true)
        setError(null)
        const formData = new FormData()
        formData.append('file', file)

        try {
            const response = await fetch('/api/v1/upload/classify', {
                method: 'POST',
                body: formData,
            })

            if (!response.ok) {
                const errData = await response.json()
                throw new Error(errData.detail || 'Classification failed')
            }

            const data = await response.json()
            setResult(data)

            // Task 5: Save to local history (not DB)
            try {
                const historyItem = {
                    timestamp: new Date().toISOString(),
                    filename: file.name,
                    result: data.violence_detected,
                    confidence: data.confidence,
                    model_used: data.model_used
                }
                const existing = localStorage.getItem('uploadHistory')
                const history = existing ? JSON.parse(existing) : []
                history.unshift(historyItem) // Add to top
                localStorage.setItem('uploadHistory', JSON.stringify(history.slice(0, 50))) // Keep last 50
            } catch (e) {
                console.error("Failed to save local history", e)
            }
        } catch (err: any) {
            console.error('Classification error:', err)
            setError(err.message || 'An unexpected error occurred')
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="max-w-3xl mx-auto">
            <div className="text-center mb-8">
                <h1 className="text-2xl font-bold text-white">Video Authenticator</h1>
                <p className="mt-2 text-slate-400">
                    Upload a video file to analyze it for violence using the currently active model.
                </p>
            </div>

            <div className="bg-slate-800 rounded-lg shadow-lg p-6 sm:p-8">
                <div className="flex justify-center rounded-lg border border-dashed border-slate-600 px-6 py-10 hover:bg-slate-700/50 transition-colors">
                    <div className="text-center">
                        <CloudArrowUpIcon className="mx-auto h-12 w-12 text-slate-400" aria-hidden="true" />
                        <div className="mt-4 flex text-sm leading-6 text-slate-400 justify-center">
                            <label
                                htmlFor="file-upload"
                                className="relative cursor-pointer rounded-md bg-slate-800 font-semibold text-indigo-400 focus-within:outline-none focus-within:ring-2 focus-within:ring-indigo-600 focus-within:ring-offset-2 focus-within:ring-offset-slate-900 hover:text-indigo-300"
                            >
                                <span>Upload a file</span>
                                <input
                                    id="file-upload"
                                    name="file-upload"
                                    type="file"
                                    className="sr-only"
                                    accept=".mp4,.mkv,.avi,.mov"
                                    ref={fileInputRef}
                                    onChange={handleFileChange}
                                />
                            </label>
                            <p className="pl-1">or drag and drop</p>
                        </div>
                        <p className="text-xs leading-5 text-slate-500">MP4, MKV, AVI up to 500MB</p>
                    </div>
                </div>

                {file && (
                    <div className="mt-4 flex items-center justify-between bg-slate-700/50 p-3 rounded-md">
                        <span className="text-sm text-white truncate">{file.name}</span>
                        <button
                            onClick={() => {
                                setFile(null)
                                setResult(null)
                                if (fileInputRef.current) fileInputRef.current.value = ''
                            }}
                            className="text-xs text-red-400 hover:text-red-300"
                        >
                            Remove
                        </button>
                    </div>
                )}

                <div className="mt-6">
                    <button
                        type="button"
                        onClick={handleClassify}
                        disabled={!file || loading}
                        className={`w-full flex justify-center items-center rounded-md px-3 py-2 text-sm font-semibold text-white shadow-sm focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 ${!file || loading
                            ? 'bg-slate-600 cursor-not-allowed'
                            : 'bg-indigo-600 hover:bg-indigo-500 focus-visible:outline-indigo-600'
                            }`}
                    >
                        {loading ? (
                            <>
                                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                </svg>
                                Processing...
                            </>
                        ) : (
                            <>
                                <DocumentMagnifyingGlassIcon className="h-5 w-5 mr-2" />
                                Classify Video
                            </>
                        )}
                    </button>
                </div>

                {error && (
                    <div className="mt-4 p-4 rounded-md bg-red-900/20 text-red-400 text-sm">
                        Error: {error}
                    </div>
                )}

                {result && (
                    <div className="mt-8 border-t border-slate-700 pt-8">
                        <h3 className="text-lg font-medium leading-6 text-white mb-4">Analysis Result</h3>
                        <div className={`rounded-lg p-6 ${result.violence_detected ? 'bg-red-900/20 ring-1 ring-red-500' : 'bg-green-900/20 ring-1 ring-green-500'}`}>
                            <div className="flex items-center justify-between mb-4">
                                <span className="text-sm font-medium text-slate-400">Verdict</span>
                                <span className={`inline-flex items-center rounded-md px-2 py-1 text-sm font-medium ring-1 ring-inset ${result.violence_detected
                                    ? 'bg-red-400/10 text-red-400 ring-red-400/20'
                                    : 'bg-green-400/10 text-green-400 ring-green-400/20'
                                    }`}>
                                    {result.violence_detected ? 'VIOLENCE DETECTED' : 'SAFE'}
                                </span>
                            </div>

                            <dl className="grid grid-cols-1 gap-x-4 gap-y-4 sm:grid-cols-2">
                                <div className="sm:col-span-1">
                                    <dt className="text-sm font-medium text-slate-400">Confidence</dt>
                                    <dd className="mt-1 text-sm text-white">{result.confidence}</dd>
                                </div>
                                <div className="sm:col-span-1">
                                    <dt className="text-sm font-medium text-slate-400">Model Used</dt>
                                    <dd className="mt-1 text-sm text-white">{result.model_used}</dd>
                                </div>
                            </dl>

                            {result.segments && result.segments.length > 0 && (
                                <div className="mt-4">
                                    <dt className="text-sm font-medium text-slate-400 mb-2">Detected Segments</dt>
                                    <dd className="text-sm text-white bg-slate-900/50 rounded p-2">
                                        {result.segments.map((seg: any, idx: number) => (
                                            <div key={idx} className="flex justify-between">
                                                <span>{seg.start} - {seg.end}</span>
                                                <span className="text-red-400">{seg.label}</span>
                                            </div>
                                        ))}
                                    </dd>
                                </div>
                            )}
                        </div>
                    </div>
                )}
            </div>
        </div>
    )
}
