import { Fragment, useState, useEffect } from 'react'
import { Dialog, Transition } from '@headlessui/react'
import {
    Bars3Icon,
    HomeIcon,
    VideoCameraIcon,
    BellAlertIcon,
    Cog6ToothIcon,
    ChartBarIcon,
    CpuChipIcon,
    DocumentMagnifyingGlassIcon
} from '@heroicons/react/24/outline'
import { Link, useLocation } from 'react-router-dom'
import clsx from 'clsx'

const navigation = [
    { name: 'Dashboard', href: '/', icon: HomeIcon },
    { name: 'Live Monitor', href: '/monitor', icon: VideoCameraIcon },
    { name: 'Alerts', href: '/alerts', icon: BellAlertIcon },
    { name: 'Models', href: '/models', icon: CpuChipIcon },
    { name: 'Authenticator', href: '/authenticator', icon: DocumentMagnifyingGlassIcon },
    { name: 'History', href: '/history', icon: ChartBarIcon },
    { name: 'Security', href: '/security', icon: Cog6ToothIcon },
]

export default function Layout({ children }: { children: React.ReactNode }) {
    const [sidebarOpen, setSidebarOpen] = useState(false)
    const [activeModel, setActiveModel] = useState<string | null>(null)
    const location = useLocation()

    useEffect(() => {
        const fetchActiveModel = async () => {
            try {
                // Use absolute URL like Dashboard which is confirmed working
                const res = await fetch('http://localhost:8000/health')
                if (res.ok) {
                    const data = await res.json()
                    // Health endpoint structure: data.services.active_model
                    if (data.services && data.services.active_model) {
                        const modelData = data.services.active_model;
                        if (typeof modelData === 'string') {
                            setActiveModel(modelData);
                        } else if (typeof modelData === 'object' && modelData.name) {
                            setActiveModel(modelData.name);
                        }
                    }
                }
            } catch (e) {
                console.error("Failed to fetch active model in layout")
            }
        }

        fetchActiveModel()
        // Poll every 2 seconds
        const interval = setInterval(fetchActiveModel, 2000)
        return () => clearInterval(interval)
    }, [])

    return (
        <div>
            <Transition.Root show={sidebarOpen} as={Fragment}>
                <Dialog as="div" className="relative z-50 lg:hidden" onClose={setSidebarOpen}>
                    <Transition.Child
                        as={Fragment}
                        enter="transition-opacity ease-linear duration-300"
                        enterFrom="opacity-0"
                        enterTo="opacity-100"
                        leave="transition-opacity ease-linear duration-300"
                        leaveFrom="opacity-100"
                        leaveTo="opacity-0"
                    >
                        <div className="fixed inset-0 bg-gray-900/80" />
                    </Transition.Child>

                    <div className="fixed inset-0 flex">
                        <Transition.Child
                            as={Fragment}
                            enter="transition ease-in-out duration-300 transform"
                            enterFrom="-translate-x-full"
                            enterTo="translate-x-0"
                            leave="transition ease-in-out duration-300 transform"
                            leaveFrom="translate-x-0"
                            leaveTo="-translate-x-full"
                        >
                            <Dialog.Panel className="relative mr-16 flex w-full max-w-xs flex-1">
                                <div className="flex grow flex-col gap-y-5 overflow-y-auto bg-slate-900 px-6 pb-4 ring-1 ring-white/10">
                                    <div className="flex h-16 shrink-0 items-center">
                                        <span className="ml-4 text-lg font-bold text-white">Violence Monitor</span>
                                    </div>
                                    <nav className="flex flex-1 flex-col">
                                        <ul role="list" className="flex flex-1 flex-col gap-y-7">
                                            <li>
                                                <ul role="list" className="-mx-2 space-y-1">
                                                    {navigation.map((item) => (
                                                        <li key={item.name}>
                                                            <Link
                                                                to={item.href}
                                                                className={clsx(
                                                                    location.pathname === item.href
                                                                        ? 'bg-slate-800 text-white'
                                                                        : 'text-slate-400 hover:text-white hover:bg-slate-800',
                                                                    'group flex gap-x-3 rounded-md p-2 text-sm leading-6 font-semibold'
                                                                )}
                                                            >
                                                                <item.icon className="h-6 w-6 shrink-0" aria-hidden="true" />
                                                                {item.name}
                                                            </Link>
                                                        </li>
                                                    ))}
                                                </ul>
                                            </li>
                                        </ul>
                                    </nav>
                                </div>
                            </Dialog.Panel>
                        </Transition.Child>
                    </div>
                </Dialog>
            </Transition.Root>

            {/* Static sidebar for desktop */}
            <div className="hidden lg:fixed lg:inset-y-0 lg:z-50 lg:flex lg:w-72 lg:flex-col">
                <div className="flex grow flex-col gap-y-5 overflow-y-auto bg-slate-900 px-6 pb-4 border-r border-slate-800">
                    <div className="flex h-16 shrink-0 items-center">
                        <span className="ml-4 text-xl font-bold text-white tracking-tight">Violence Monitor</span>
                    </div>
                    <nav className="flex flex-1 flex-col">
                        <ul role="list" className="flex flex-1 flex-col gap-y-7">
                            <li>
                                <ul role="list" className="-mx-2 space-y-1">
                                    {navigation.map((item) => (
                                        <li key={item.name}>
                                            <Link
                                                to={item.href}
                                                className={clsx(
                                                    location.pathname === item.href
                                                        ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-500/20'
                                                        : 'text-slate-400 hover:text-white hover:bg-slate-800',
                                                    'group flex gap-x-3 rounded-md p-2 text-sm leading-6 font-semibold transition-all duration-200'
                                                )}
                                            >
                                                <item.icon className="h-6 w-6 shrink-0" aria-hidden="true" />
                                                {item.name}
                                            </Link>
                                        </li>
                                    ))}
                                </ul>
                            </li>
                        </ul>
                    </nav>
                </div>
            </div>

            <div className="lg:pl-72">
                <div className="sticky top-0 z-40 flex h-16 shrink-0 items-center gap-x-4 border-b border-slate-800 bg-slate-900/50 backdrop-blur-md px-4 shadow-sm sm:gap-x-6 sm:px-6 lg:px-8">
                    <button
                        type="button"
                        className="-m-2.5 p-2.5 text-slate-400 lg:hidden"
                        onClick={() => setSidebarOpen(true)}
                    >
                        <span className="sr-only">Open sidebar</span>
                        <Bars3Icon className="h-6 w-6" aria-hidden="true" />
                    </button>

                    <div className="flex flex-1 gap-x-4 self-stretch lg:gap-x-6">
                        <div className="flex flex-1 items-center">
                            <h1 className="text-lg font-semibold text-white">
                                {navigation.find(n => n.href === location.pathname)?.name || 'Dashboard'}
                            </h1>
                        </div>
                        <div className="flex items-center gap-x-4 lg:gap-x-6">
                            <button type="button" className="-m-2.5 p-2.5 text-slate-400 hover:text-slate-300">
                                <span className="sr-only">View notifications</span>
                                <BellAlertIcon className="h-6 w-6" aria-hidden="true" />
                            </button>
                            <div className="hidden lg:block lg:h-6 lg:w-px lg:bg-slate-800" aria-hidden="true" />
                            <div className="flex items-center gap-x-4">
                                <div className="hidden md:flex items-center px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-xs font-medium">
                                    <CpuChipIcon className="w-4 h-4 mr-2" />
                                    Active Model: {activeModel || 'Loading...'}
                                </div>
                                <span className="text-sm font-semibold leading-6 text-white">Admin User</span>
                            </div>
                        </div>
                    </div>
                </div>

                <main className="py-10">
                    <div className="px-4 sm:px-6 lg:px-8">
                        {children}
                    </div>
                </main>
            </div>
        </div>
    )
}
