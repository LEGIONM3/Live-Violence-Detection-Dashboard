import { useEffect, useState } from 'react'
import { CheckCircleIcon, CpuChipIcon } from '@heroicons/react/24/outline'

interface Model {
    name: string
    path: string
    type: string
}

export default function Models() {
    const [models, setModels] = useState<Model[]>([])
    const [activeModel, setActiveModel] = useState<string | null>(null)
    const [loading, setLoading] = useState(false)

    useEffect(() => {
        fetchModels()
        fetchActiveModel()
    }, [])

    const fetchModels = () => {
        fetch('/api/v1/models/')
            .then(res => res.json())
            .then(data => {
                if (Array.isArray(data)) {
                    setModels(data)
                } else {
                    console.error("Invalid models format received:", data)
                    setModels([])
                }
            })
            .catch(err => {
                console.error("Failed to fetch models:", err)
                setModels([])
            })
    }

    const fetchActiveModel = () => {
        fetch('/api/v1/models/active')
            .then(res => res.json())
            .then(data => setActiveModel(data.active_model))
            .catch(console.error)
    }

    const handleActivate = (modelName: string) => {
        setLoading(true)
        fetch(`/api/v1/models/active?model_name=${encodeURIComponent(modelName)}`, {
            method: 'POST',
        })
            .then(res => res.json())
            .then(data => {
                if (data.status === 'success') {
                    setActiveModel(data.active_model)
                }
            })
            .catch(console.error)
            .finally(() => setLoading(false))
    }

    return (
        <div>
            <div className="sm:flex sm:items-center">
                <div className="sm:flex-auto">
                    <h1 className="text-base font-semibold leading-6 text-white">AI Models</h1>
                    <p className="mt-2 text-sm text-slate-400">
                        Manage and select the active deep learning model for violence detection.
                    </p>
                </div>
            </div>

            <div className="mt-8 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
                {models.map((model) => (
                    <div
                        key={model.name}
                        className={`relative flex flex-col rounded-lg border p-6 shadow-sm transition-all ${activeModel === model.name
                            ? 'border-indigo-500 bg-indigo-500/10 ring-1 ring-indigo-500'
                            : 'border-slate-700 bg-slate-800 hover:border-slate-600'
                            }`}
                    >
                        <div className="flex items-center justify-between">
                            <div className="flex items-center">
                                <div className={`rounded-md p-2 ${activeModel === model.name ? 'bg-indigo-500' : 'bg-slate-700'}`}>
                                    <CpuChipIcon className="h-6 w-6 text-white" aria-hidden="true" />
                                </div>
                                <h3 className="ml-3 text-sm font-semibold text-white">{model.name}</h3>
                            </div>
                            {activeModel === model.name && (
                                <CheckCircleIcon className="h-6 w-6 text-indigo-400" aria-hidden="true" />
                            )}
                        </div>

                        <div className="mt-4 flex flex-1 flex-col justify-between">
                            <div className="text-sm text-slate-400">
                                <p>Type: <span className="uppercase">{model.type}</span></p>
                                <p className="mt-1 truncate" title={model.path}>Path: {model.path}</p>
                            </div>

                            <div className="mt-6">
                                <button
                                    type="button"
                                    onClick={() => handleActivate(model.name)}
                                    disabled={loading || activeModel === model.name}
                                    className={`w-full rounded-md px-3 py-2 text-sm font-semibold shadow-sm focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 ${activeModel === model.name
                                        ? 'cursor-default bg-green-600 text-white hover:bg-green-500'
                                        : 'bg-indigo-600 text-white hover:bg-indigo-500 focus-visible:outline-indigo-600'
                                        }`}
                                >
                                    {activeModel === model.name ? 'Active Model' : 'Activate Model'}
                                </button>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    )
}
