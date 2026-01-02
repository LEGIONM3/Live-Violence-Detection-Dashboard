import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Layout from './layouts/Layout'
import Dashboard from './pages/Dashboard'
import LiveMonitor from './pages/LiveMonitor'
import Alerts from './pages/Alerts'

import Models from './pages/Models'
import Authenticator from './pages/Authenticator'
import Security from './pages/Security'
import History from './pages/History'

import Settings from './pages/Settings'

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/monitor" element={<LiveMonitor />} />
          <Route path="/alerts" element={<Alerts />} />
          <Route path="/models" element={<Models />} />
          <Route path="/authenticator" element={<Authenticator />} />
          <Route path="/history" element={<History />} />
          <Route path="/security" element={<Security />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </Layout>
    </Router>
  )
}

export default App