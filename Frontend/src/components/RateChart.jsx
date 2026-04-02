import { useCallback } from 'react'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer,
} from 'recharts'
import { useFetch } from '../hooks/useFetch'
import { getRateHistory } from '../services/api'

function toYYYYMMDD(date) {
  return date.toISOString().split('T')[0]
}

function getLast30Days() {
  const to   = new Date()
  const from = new Date()
  from.setDate(from.getDate() - 30)
  return { from: toYYYYMMDD(from), to: toYYYYMMDD(to) }
}

const LINE_COLOR = '#4f8ef7'

export default function RateChart({ provider, rateType }) {
  const { from, to } = getLast30Days()

  const fetcher = useCallback(
    () => getRateHistory({ provider, type: rateType, from, to, page_size: 500 }),
    [provider, rateType, from, to]
  )

  const { data, loading, error, refetch } = useFetch(fetcher, [provider, rateType])

  const chartData = data?.results
    ? [...data.results]
        .sort((a, b) => a.effective_date.localeCompare(b.effective_date))
        .map(r => ({
          date:  r.effective_date,
          rate:  Number(r.rate_value),
          label: `${r.provider_name} — ${r.rate_type}`,
        }))
    : []

  const title = [provider, rateType].filter(Boolean).join(' / ') || 'All providers & types'

  return (
    <section className="card">
      <div className="card-header">
        <h2>30-Day History</h2>
        <div className="header-meta">
          <span className="refresh-note">{title}</span>
          <button className="btn-icon" onClick={refetch} title="Refresh now">↻</button>
        </div>
      </div>

      {loading && (
        <div className="state-box loading">
          <div className="spinner" />
          <p>Loading rate history…</p>
        </div>
      )}

      {error && !loading && (
        <div className="state-box error">
          <span className="state-icon">⚠</span>
          <p><strong>Failed to load history</strong></p>
          <p className="error-detail">{error}</p>
          <button className="btn-retry" onClick={refetch}>Retry</button>
        </div>
      )}

      {!loading && !error && chartData.length === 0 && (
        <div className="state-box empty">
          <span className="state-icon">📉</span>
          <p>No history data for the selected filters in the last 30 days.</p>
        </div>
      )}

      {!loading && !error && chartData.length > 0 && (
        <div className="chart-wrapper">
          <ResponsiveContainer width="100%" height={320}>
            <LineChart data={chartData} margin={{ top: 8, right: 24, left: 0, bottom: 8 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis
                dataKey="date"
                tick={{ fontSize: 11 }}
                tickFormatter={d => d.slice(5)} // show MM-DD
              />
              <YAxis
                tick={{ fontSize: 11 }}
                tickFormatter={v => `${v}%`}
                domain={['auto', 'auto']}
              />
              <Tooltip
                formatter={(value) => [`${value.toFixed(2)}%`, 'Rate']}
                labelFormatter={label => `Date: ${label}`}
              />
              <Legend />
              <Line
                type="monotone"
                dataKey="rate"
                name="Rate Value"
                stroke={LINE_COLOR}
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 5 }}
              />
            </LineChart>
          </ResponsiveContainer>
          <p className="row-count">{chartData.length} data point{chartData.length !== 1 ? 's' : ''}</p>
        </div>
      )}
    </section>
  )
}
