import { useEffect, useState } from 'react'
import { ArrowUpIcon, ArrowDownIcon } from '@heroicons/react/20/solid'
import { VideoCameraIcon, ExclamationTriangleIcon, ServerIcon } from '@heroicons/react/24/outline'

const stats = [
    { id: 1, name: 'Active Cameras', stat: '4', icon: VideoCameraIcon, change: '1', changeType: 'increase' },
    { id: 2, name: 'Total Alerts (24h)', stat: '12', icon: ExclamationTriangleIcon, change: '3', changeType: 'decrease' },
    { id: 3, name: 'System Status', stat: 'Online', icon: ServerIcon, change: '99.9%', changeType: 'increase' },
]

function classNames(...classes: string[]) {
    return classes.filter(Boolean).join(' ')
}

export default function Dashboard() {
    const [health, setHealth] = useState<any>(null)

    useEffect(() => {
        fetch('http://localhost:8000/health')
            .then(res => res.json())
            .then(data => setHealth(data))
            .catch(console.error)
    }, [])

    return (
        <div>
            <h3 className="text-base font-semibold leading-6 text-white">Last 30 Days</h3>

            <dl className="mt-5 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
                {stats.map((item) => (
                    <div
                        key={item.id}
                        className="relative overflow-hidden rounded-lg bg-slate-800 px-4 pb-12 pt-5 shadow sm:px-6 sm:pt-6"
                    >
                        <dt>
                            <div className="absolute rounded-md bg-indigo-500 p-3">
                                <item.icon className="h-6 w-6 text-white" aria-hidden="true" />
                            </div>
                            <p className="ml-16 truncate text-sm font-medium text-slate-400">{item.name}</p>
                        </dt>
                        <dd className="ml-16 flex items-baseline pb-1 sm:pb-7">
                            <p className="text-2xl font-semibold text-white">{item.stat}</p>
                            <p
                                className={classNames(
                                    item.changeType === 'increase' ? 'text-green-400' : 'text-red-400',
                                    'ml-2 flex items-baseline text-sm font-semibold'
                                )}
                            >
                                {item.changeType === 'increase' ? (
                                    <ArrowUpIcon className="h-5 w-5 flex-shrink-0 self-center text-green-400" aria-hidden="true" />
                                ) : (
                                    <ArrowDownIcon className="h-5 w-5 flex-shrink-0 self-center text-red-400" aria-hidden="true" />
                                )}
                                <span className="sr-only"> {item.changeType === 'increase' ? 'Increased' : 'Decreased'} by </span>
                                {item.change}
                            </p>
                        </dd>
                    </div>
                ))}
            </dl>

            <div className="mt-8">
                <h3 className="text-lg font-medium leading-6 text-white mb-4">System Health</h3>
                <div className="bg-slate-800 shadow sm:rounded-lg">
                    <div className="px-4 py-5 sm:p-6">
                        <div className="grid grid-cols-1 gap-x-4 gap-y-8 sm:grid-cols-2">
                            <div className="sm:col-span-1">
                                <dt className="text-sm font-medium text-slate-400">Backend Version</dt>
                                <dd className="mt-1 text-sm text-white">{health?.version || 'Loading...'}</dd>
                            </div>
                            <div className="sm:col-span-1">
                                <dt className="text-sm font-medium text-slate-400">Active Model</dt>
                                <dd className="mt-1 text-sm text-white">
                                    {typeof health?.services?.active_model === 'string'
                                        ? health.services.active_model
                                        : health?.services?.active_model?.name || 'None'}
                                </dd>
                            </div>
                            <div className="sm:col-span-1">
                                <dt className="text-sm font-medium text-slate-400">Database</dt>
                                <dd className="mt-1 text-sm text-green-400">Connected</dd>
                            </div>
                            <div className="sm:col-span-1">
                                <dt className="text-sm font-medium text-slate-400">Redis</dt>
                                <dd className="mt-1 text-sm text-green-400">Connected</dd>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}
