import { useState, useCallback } from 'react'
import RateTable from './components/RateTable'
import RateChart from './components/RateChart'
import Filters   from './components/Filters'
import { useFetch } from './hooks/useFetch'
import { getLatestRates } from './services/api'
import './App.css'

export default function App() {
  // Filter state
  const [tableTypeFilter, setTableTypeFilter] = useState('')
  const [chartProvider,   setChartProvider]   = useState('')
  const [chartType,       setChartType]       = useState('')

  // Load latest rates once to populate filter dropdowns
  const seedFetcher = useCallback(() => getLatestRates(), [])
  const { data: seedData } = useFetch(seedFetcher, [])

  const rateTypes = seedData
    ? [...new Set(seedData.map(r => r.rate_type))].sort()
    : []
  const providers = seedData
    ? [...new Set(seedData.map(r => r.provider_name))].sort()
    : []

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-inner">
          <div className="logo">
            <span className="logo-icon">📈</span>
            <span className="logo-text">Rate Tracker</span>
          </div>
          <span className="header-sub">Real-time interest rate dashboard</span>
        </div>
      </header>

      <main className="app-main">
        <Filters
          tableTypeFilter={tableTypeFilter}
          onTableTypeChange={setTableTypeFilter}
          chartProvider={chartProvider}
          onChartProvider={setChartProvider}
          chartType={chartType}
          onChartType={setChartType}
          rateTypes={rateTypes}
          providers={providers}
        />

        <RateTable typeFilter={tableTypeFilter} />
        <RateChart provider={chartProvider} rateType={chartType} />
      </main>

      <footer className="app-footer">
        <p>Rate Tracker &copy; {new Date().getFullYear()} — data from <code>http://127.0.0.1:8000</code></p>
      </footer>
    </div>
  )
}
