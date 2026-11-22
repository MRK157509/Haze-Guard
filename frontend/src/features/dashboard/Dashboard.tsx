import { useMemo, useState, type ReactNode } from 'react'
import type { ObservationFilters } from '../../types/observation'
import { useObservations } from './useObservations'

const formatTime = (timestamp: string) => new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(timestamp))
const confidenceLabel = (value: number) => `${value.toFixed(1)} / 10`
const emptyObservations: never[] = []

export function Dashboard() {
  const [filters, setFilters] = useState<ObservationFilters>({ limit: 50 })
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const { data, error, loading, reload } = useObservations(filters)
  const observations = data?.items ?? emptyObservations
  const nodes = useMemo(() => [...new Set(observations.map(({ node_id }) => node_id))].sort(), [observations])
  const spoofing = observations.filter(({ signal_type }) => signal_type === 'spoofing')
  const jamming = observations.filter(({ signal_type }) => signal_type === 'jamming')
  const selected = observations.find(({ id }) => id === selectedId) ?? null
  const setFilter = (key: keyof ObservationFilters, value: string) => setFilters(current => ({ ...current, [key]: value || undefined, offset: 0 }))

  return <main className="dashboard-shell">
    <header className="topbar"><div><p className="eyebrow">GNSS SECURITY OPERATIONS</p><h1>HazeGuard</h1><p className="subtle">Detection intelligence for spoofing and jamming observations.</p></div><button className="refresh" onClick={() => void reload()} disabled={loading}>{loading ? 'Refreshing…' : 'Refresh data'}</button></header>
    <section className="filters" aria-label="Observation filters">
      <label>Node<select value={filters.node_id ?? ''} onChange={event => setFilter('node_id', event.target.value)}><option value="">All nodes</option>{nodes.map(node => <option key={node}>{node}</option>)}</select></label>
      <label>Signal<select value={filters.signal_type ?? ''} onChange={event => setFilter('signal_type', event.target.value)}><option value="">All signals</option><option value="spoofing">Spoofing</option><option value="jamming">Jamming</option></select></label>
      <label>From<input type="datetime-local" onChange={event => setFilter('start_time', event.target.value ? new Date(event.target.value).toISOString() : '')} /></label>
      <label>To<input type="datetime-local" onChange={event => setFilter('end_time', event.target.value ? new Date(event.target.value).toISOString() : '')} /></label>
    </section>
    {loading && <StatusPanel title="Loading observations" message="Connecting to the FastAPI observation service…" />}
    {error && <StatusPanel title="Data unavailable" message={error} action={<button className="refresh" onClick={() => void reload()}>Try again</button>} />}
    {!loading && !error && observations.length === 0 && <StatusPanel title="No observations found" message="No stored GNSS observations match the active filters." />}
    {!loading && !error && observations.length > 0 && <>
      <section className="metric-grid" aria-label="Observation overview">
        <Metric label="Observations" value={String(observations.length)} note="Current result set" />
        <Metric label="Spoofing detections" value={String(spoofing.length)} tone="amber" note="Classified spoofing" />
        <Metric label="Jamming detections" value={String(jamming.length)} tone="violet" note="Classified jamming" />
        <Metric label="Detection nodes" value={String(nodes.length)} tone="cyan" note="Reporting in this result set" />
      </section>
      <section className="content-grid">
        <section className="panel recent"><div className="panel-heading"><div><p className="eyebrow">LIVE RECORD</p><h2>Recent GNSS observations</h2></div><span>{data?.limit ?? 0} per page</span></div><div className="table-wrap"><table><thead><tr><th>Observation</th><th>Node</th><th>Confidence</th><th>Location</th></tr></thead><tbody>{observations.map(observation => <tr key={observation.id} className={selectedId === observation.id ? 'selected' : ''} onClick={() => setSelectedId(observation.id)}><td><span className={`badge ${observation.signal_type}`}>{observation.signal_type}</span><small>{formatTime(observation.timestamp)}</small></td><td>{observation.node_id}</td><td><Confidence value={observation.confidence} /></td><td>{observation.coordinates.lat.toFixed(4)}, {observation.coordinates.lon.toFixed(4)}</td></tr>)}</tbody></table></div></section>
        <aside className="panel detail"><p className="eyebrow">OBSERVATION DETAILS</p>{selected ? <><h2>{selected.signal_type}</h2><Confidence value={selected.confidence} full /><dl><dt>Node</dt><dd>{selected.node_id}</dd><dt>Observed</dt><dd>{formatTime(selected.timestamp)}</dd><dt>Coordinates</dt><dd>{selected.coordinates.lat}, {selected.coordinates.lon}</dd><dt>Metadata</dt><dd><code>{JSON.stringify(selected.metadata)}</code></dd></dl></> : <><h2>Select an observation</h2><p className="subtle">Choose a row to inspect its approved observation fields.</p></>}</aside>
      </section>
    </>}
  </main>
}

function Metric({ label, value, note, tone = 'default' }: { label: string; value: string; note: string; tone?: string }) { return <article className={`metric ${tone}`}><p>{label}</p><strong>{value}</strong><span>{note}</span></article> }
function Confidence({ value, full = false }: { value: number; full?: boolean }) { return <div className={full ? 'confidence full' : 'confidence'}><span>{confidenceLabel(value)}</span><div aria-label={`Confidence ${confidenceLabel(value)}`} className="confidence-track"><i style={{ width: `${value * 10}%` }} /></div></div> }
function StatusPanel({ title, message, action }: { title: string; message: string; action?: ReactNode }) { return <section className="status-panel" role="status"><h2>{title}</h2><p>{message}</p>{action}</section> }
