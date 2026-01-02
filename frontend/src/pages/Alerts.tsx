import { ExclamationTriangleIcon } from '@heroicons/react/24/outline'

const alerts = [
    {
        id: 1,
        camera: 'Parking Lot A',
        timestamp: '2025-12-05 22:15:30',
        type: 'Violence Detected',
        confidence: '98%',
        status: 'New',
        thumbnail: 'https://via.placeholder.com/150/FF0000/FFFFFF?text=Violence'
    },
    {
        id: 2,
        camera: 'Back Alley',
        timestamp: '2025-12-05 21:45:12',
        type: 'Suspicious Activity',
        confidence: '85%',
        status: 'Reviewed',
        thumbnail: 'https://via.placeholder.com/150/FFFF00/000000?text=Suspicious'
    },
    {
        id: 3,
        camera: 'Entrance Hall',
        timestamp: '2025-12-05 18:30:00',
        type: 'Violence Detected',
        confidence: '92%',
        status: 'Resolved',
        thumbnail: 'https://via.placeholder.com/150/FF0000/FFFFFF?text=Violence'
    },
]

export default function Alerts() {
    return (
        <div>
            <div className="sm:flex sm:items-center">
                <div className="sm:flex-auto">
                    <h1 className="text-base font-semibold leading-6 text-white">Alerts</h1>
                    <p className="mt-2 text-sm text-slate-400">
                        A list of all detected security alerts including timestamp, camera location, and confidence score.
                    </p>
                </div>
                <div className="mt-4 sm:ml-16 sm:mt-0 sm:flex-none">
                    <button
                        type="button"
                        className="block rounded-md bg-indigo-600 px-3 py-2 text-center text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
                    >
                        Export Log
                    </button>
                </div>
            </div>
            <div className="mt-8 flow-root">
                <div className="-mx-4 -my-2 overflow-x-auto sm:-mx-6 lg:-mx-8">
                    <div className="inline-block min-w-full py-2 align-middle sm:px-6 lg:px-8">
                        <table className="min-w-full divide-y divide-slate-700">
                            <thead>
                                <tr>
                                    <th scope="col" className="py-3.5 pl-4 pr-3 text-left text-sm font-semibold text-white sm:pl-0">
                                        ID
                                    </th>
                                    <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-white">
                                        Thumbnail
                                    </th>
                                    <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-white">
                                        Type
                                    </th>
                                    <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-white">
                                        Camera
                                    </th>
                                    <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-white">
                                        Timestamp
                                    </th>
                                    <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-white">
                                        Confidence
                                    </th>
                                    <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-white">
                                        Status
                                    </th>
                                    <th scope="col" className="relative py-3.5 pl-3 pr-4 sm:pr-0">
                                        <span className="sr-only">Actions</span>
                                    </th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-800">
                                {alerts.map((alert) => (
                                    <tr key={alert.id}>
                                        <td className="whitespace-nowrap py-4 pl-4 pr-3 text-sm font-medium text-white sm:pl-0">
                                            #{alert.id}
                                        </td>
                                        <td className="whitespace-nowrap px-3 py-4 text-sm text-slate-300">
                                            <img src={alert.thumbnail} alt="Alert" className="h-10 w-16 object-cover rounded" />
                                        </td>
                                        <td className="whitespace-nowrap px-3 py-4 text-sm text-slate-300">
                                            <div className="flex items-center">
                                                <ExclamationTriangleIcon className={`h-5 w-5 mr-2 ${alert.type.includes('Violence') ? 'text-red-500' : 'text-yellow-500'}`} />
                                                {alert.type}
                                            </div>
                                        </td>
                                        <td className="whitespace-nowrap px-3 py-4 text-sm text-slate-300">{alert.camera}</td>
                                        <td className="whitespace-nowrap px-3 py-4 text-sm text-slate-300">{alert.timestamp}</td>
                                        <td className="whitespace-nowrap px-3 py-4 text-sm text-slate-300">{alert.confidence}</td>
                                        <td className="whitespace-nowrap px-3 py-4 text-sm text-slate-300">
                                            <span className={`inline-flex items-center rounded-md px-2 py-1 text-xs font-medium ring-1 ring-inset ${alert.status === 'New' ? 'bg-red-400/10 text-red-400 ring-red-400/20' :
                                                    alert.status === 'Resolved' ? 'bg-green-400/10 text-green-400 ring-green-400/20' :
                                                        'bg-yellow-400/10 text-yellow-400 ring-yellow-400/20'
                                                }`}>
                                                {alert.status}
                                            </span>
                                        </td>
                                        <td className="relative whitespace-nowrap py-4 pl-3 pr-4 text-right text-sm font-medium sm:pr-0">
                                            <a href="#" className="text-indigo-400 hover:text-indigo-300">
                                                Review<span className="sr-only">, {alert.id}</span>
                                            </a>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    )
}
