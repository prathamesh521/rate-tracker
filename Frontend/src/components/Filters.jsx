
export default function Filters({
  tableTypeFilter,
  onTableTypeChange,
  chartProvider,
  onChartProvider,
  chartType,
  onChartType,
  rateTypes = [],
  providers = [],
}) {
  return (
    <section className="filters-bar">
      <div className="filter-group">
        <label htmlFor="table-type-filter">Table — Rate Type</label>
        <select
          id="table-type-filter"
          value={tableTypeFilter}
          onChange={e => onTableTypeChange(e.target.value)}
        >
          <option value="">All types</option>
          {rateTypes.map(t => (
            <option key={t} value={t}>{t}</option>
          ))}
        </select>
      </div>

      <div className="filter-divider" />

      <div className="filter-group">
        <label htmlFor="chart-provider">Chart — Provider</label>
        <select
          id="chart-provider"
          value={chartProvider}
          onChange={e => onChartProvider(e.target.value)}
        >
          <option value="">All providers</option>
          {providers.map(p => (
            <option key={p} value={p}>{p}</option>
          ))}
        </select>
      </div>

      <div className="filter-group">
        <label htmlFor="chart-type">Chart — Rate Type</label>
        <select
          id="chart-type"
          value={chartType}
          onChange={e => onChartType(e.target.value)}
        >
          <option value="">All types</option>
          {rateTypes.map(t => (
            <option key={t} value={t}>{t}</option>
          ))}
        </select>
      </div>
    </section>
  )
}
