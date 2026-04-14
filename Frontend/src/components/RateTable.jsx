import { useState, useEffect } from 'react'
import { getLatestRates } from '../services/api'

export default function RateTable() {
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [typeFilter, setTypeFilter] = useState('')
  const [providerFilter, setProviderFilter] = useState('')

  useEffect(() => {
    setLoading(true)
    setError(null)
    getLatestRates(typeFilter)
      .then(setData)
      .catch(err => setError(err.message))
      .finally(() => setLoading(false))
  }, [typeFilter])

  const rateTypes = [...new Set(data.map(r => r.rate_type))].sort()
  const providers = [...new Set(data.map(r => r.provider_name))].sort()

  const rows = providerFilter
    ? data.filter(r => r.provider_name === providerFilter)
    : data

  return (
    <div className="table-card">
      <div className="table-header">
        <h2>Latest Rates</h2>
        <div className="filters">
          <select value={typeFilter} onChange={e => { setTypeFilter(e.target.value); setProviderFilter('') }}>
            <option value="">All Rate Types</option>
            {rateTypes.map(t => <option key={t} value={t}>{t}</option>)}
          </select>
          <select value={providerFilter} onChange={e => setProviderFilter(e.target.value)}>
            <option value="">All Providers</option>
            {providers.map(p => <option key={p} value={p}>{p}</option>)}
          </select>
        </div>
      </div>

      {loading && <div className="state-msg">Loading...</div>}
      {error && <div className="state-msg error">Error: {error}</div>}

      {!loading && !error && (
        <>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Provider</th>
                  <th>Rate Type</th>
                  <th>Rate Value</th>
                  <th>Effective Date</th>
                </tr>
              </thead>
              <tbody>
                {rows.length === 0 ? (
                  <tr><td colSpan="4" className="empty-row">No records found.</td></tr>
                ) : rows.map(row => (
                  <tr key={row.id}>
                    <td>{row.provider_name}</td>
                    <td><span className="badge">{row.rate_type}</span></td>
                    <td className="rate-value">{Number(row.rate_value).toFixed(2)}%</td>
                    <td>{row.effective_date}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="row-count">{rows.length} record{rows.length !== 1 ? 's' : ''}</div>
        </>
      )}
    </div>
  )
}
