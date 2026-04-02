import { useState, useCallback } from 'react'
import { useFetch } from '../hooks/useFetch'
import { getLatestRates } from '../services/api'

const AUTO_REFRESH_MS = 60_000

const COLUMNS = [
  { key: 'provider_name', label: 'Provider' },
  { key: 'rate_type',     label: 'Rate Type' },
  { key: 'rate_value',    label: 'Rate Value', numeric: true },
  { key: 'effective_date', label: 'Effective Date' },
]

function SortIcon({ direction }) {
  if (!direction) return <span className="sort-icon neutral">⇅</span>
  return (
    <span className="sort-icon active">
      {direction === 'asc' ? '↑' : '↓'}
    </span>
  )
}

export default function RateTable({ typeFilter }) {
  const [sort, setSort] = useState({ key: null, direction: null })

  const fetcher = useCallback(
    () => getLatestRates(typeFilter),
    [typeFilter]
  )

  const { data, loading, error, refetch } = useFetch(fetcher, [typeFilter], AUTO_REFRESH_MS)

  function handleSort(key) {
    setSort(prev => {
      if (prev.key !== key) return { key, direction: 'asc' }
      if (prev.direction === 'asc') return { key, direction: 'desc' }
      return { key: null, direction: null }
    })
  }

  const rows = data ? [...data] : []

  if (sort.key) {
    rows.sort((a, b) => {
      const av = a[sort.key]
      const bv = b[sort.key]
      const cmp = typeof av === 'number'
        ? av - bv
        : String(av).localeCompare(String(bv))
      return sort.direction === 'asc' ? cmp : -cmp
    })
  }

  return (
    <section className="card">
      <div className="card-header">
        <h2>Latest Rates</h2>
        <div className="header-meta">
          <span className="refresh-note">Auto-refreshes every 60s</span>
          <button className="btn-icon" onClick={refetch} title="Refresh now">↻</button>
        </div>
      </div>

      {loading && (
        <div className="state-box loading">
          <div className="spinner" />
          <p>Loading latest rates…</p>
        </div>
      )}

      {error && !loading && (
        <div className="state-box error">
          <span className="state-icon">⚠</span>
          <p><strong>Failed to load rates</strong></p>
          <p className="error-detail">{error}</p>
          <button className="btn-retry" onClick={refetch}>Retry</button>
        </div>
      )}

      {!loading && !error && rows.length === 0 && (
        <div className="state-box empty">
          <span className="state-icon">📭</span>
          <p>No rates found{typeFilter ? ` for type "${typeFilter}"` : ''}.</p>
        </div>
      )}

      {!loading && !error && rows.length > 0 && (
        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                {COLUMNS.map(col => (
                  <th
                    key={col.key}
                    className={col.numeric ? 'num' : ''}
                    onClick={() => handleSort(col.key)}
                  >
                    {col.label}
                    <SortIcon direction={sort.key === col.key ? sort.direction : null} />
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map(row => (
                <tr key={row.id}>
                  <td>{row.provider_name}</td>
                  <td><span className="badge">{row.rate_type}</span></td>
                  <td className="num">{Number(row.rate_value).toFixed(2)}%</td>
                  <td>{row.effective_date}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="row-count">{rows.length} record{rows.length !== 1 ? 's' : ''}</p>
        </div>
      )}
    </section>
  )
}
