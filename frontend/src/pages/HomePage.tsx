import { useEffect, useRef, useState } from 'react'
import { api, money, type JobRow } from '../api'
import { ErrorBanner, StatusPill, Stepper } from '../components/ui'
import { href, navigate } from '../router'

// Display order and descriptions for the bundled demo reports.
const SAMPLE_INFO: Record<string, { title: string; blurb: string }> = {
  'demo_a_1428_maple_ave.pdf': { title: 'Demo Provider A report', blurb: 'Known layout, clean data. Should verify straight through.' },
  'demo_b_77_ridgeview_dr.pdf': { title: 'Demo Provider B report', blurb: 'Different layout, areas in squares, steep 9/12 & 12/12 sections.' },
  'demo_a_needs_review_oak_st.pdf': { title: 'Report with problems', blurb: 'Missing eaves and pitch areas that don’t add up. Verification blocks it.' },
  'field_worksheet_unknown_format.pdf': { title: 'Unknown format', blurb: 'Free-text field worksheet. Generic parser + AI fallback, flagged for review.' },
}

export default function HomePage() {
  const [jobs, setJobs] = useState<JobRow[]>([])
  const [samples, setSamples] = useState<string[]>([])
  const [aiEnabled, setAiEnabled] = useState(false)
  const [useAi, setUseAi] = useState(true)
  const [jobName, setJobName] = useState('')
  const [busy, setBusy] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [dragging, setDragging] = useState(false)
  const fileInput = useRef<HTMLInputElement>(null)

  useEffect(() => {
    api.jobs().then(setJobs).catch((e) => setError(e.message))
    api
      .samples()
      .then((s) => {
        const order = Object.keys(SAMPLE_INFO)
        const rank = (n: string) => (order.includes(n) ? order.indexOf(n) : order.length)
        setSamples(s.map((x) => x.name).sort((a, b) => rank(a) - rank(b)))
      })
      .catch(() => {})
    api.health().then((h) => setAiEnabled(h.ai_enabled)).catch(() => {})
  }, [])

  const run = async (label: string, fn: () => Promise<{ id: number }>) => {
    setBusy(label)
    setError(null)
    try {
      const report = await fn()
      navigate({ page: 'report', id: report.id })
    } catch (e) {
      setError((e as Error).message)
      setBusy(null)
    }
  }

  const onFile = (file: File | undefined) => {
    if (!file) return
    run(`Reading ${file.name}…`, () => api.upload(file, jobName, aiEnabled && useAi))
  }

  return (
    <>
      <Stepper step={1} />
      <ErrorBanner error={error} />
      <div className="grid-2">
        <section className="card">
          <h2>New estimate from a measurement report</h2>
          <p className="muted">Upload a roof measurement PDF. EstimateAI detects the provider, extracts every measurement, checks it, and builds a material & labor estimate.</p>
          <label className="field">
            <span>Job name (optional)</span>
            <input value={jobName} onChange={(e) => setJobName(e.target.value)} placeholder="e.g. Smith re-roof" />
          </label>
          <div
            className={`dropzone ${dragging ? 'dragging' : ''}`}
            onClick={() => fileInput.current?.click()}
            onDragOver={(e) => {
              e.preventDefault()
              setDragging(true)
            }}
            onDragLeave={() => setDragging(false)}
            onDrop={(e) => {
              e.preventDefault()
              setDragging(false)
              onFile(e.dataTransfer.files[0])
            }}
          >
            {busy ? (
              <span className="spinner-row">
                <span className="spinner" /> {busy}
              </span>
            ) : (
              <>
                <strong>Drop a PDF here</strong>
                <span className="muted">or click to choose a file</span>
              </>
            )}
            <input ref={fileInput} type="file" accept="application/pdf" hidden onChange={(e) => onFile(e.target.files?.[0])} />
          </div>
          <label className="toggle">
            <input type="checkbox" checked={aiEnabled && useAi} disabled={!aiEnabled} onChange={(e) => setUseAi(e.target.checked)} />
            <span>
              Use AI for report formats without a template
              <span className="muted small block">
                {aiEnabled ? 'AI only reads values; every calculation is done by the estimating engine.' : 'Set ANTHROPIC_API_KEY on the server to enable.'}
              </span>
            </span>
          </label>
        </section>

        <section className="card">
          <h2>Try a sample report</h2>
          <p className="muted">Demo reports in different (fictional) provider formats.</p>
          <ul className="samples">
            {samples.map((name) => (
              <li key={name}>
                <div>
                  <strong>{SAMPLE_INFO[name]?.title ?? name}</strong>
                  <span className="muted small">{SAMPLE_INFO[name]?.blurb}</span>
                </div>
                <div className="sample-actions">
                  <a className="btn btn-ghost" href={`/api/samples/${name}`} target="_blank" rel="noreferrer">
                    View PDF
                  </a>
                  <button className="btn" disabled={!!busy} onClick={() => run(`Reading ${name}…`, () => api.loadSample(name))}>
                    Use sample
                  </button>
                </div>
              </li>
            ))}
          </ul>
        </section>
      </div>

      <section className="card">
        <h2>Recent jobs</h2>
        {jobs.length === 0 ? (
          <p className="muted">No jobs yet. Upload a report or try a sample above.</p>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>Job</th>
                <th>Report</th>
                <th>Measurements</th>
                <th className="num">Selling price</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {jobs.map((j) => (
                <tr key={j.id}>
                  <td>{j.name}</td>
                  <td className="muted">{j.provider_name}</td>
                  <td>
                    <StatusPill status={j.status} />
                  </td>
                  <td className="num">{j.selling_price !== null ? money(j.selling_price, false) : '—'}</td>
                  <td className="actions">
                    {j.report_id && <a href={href({ page: 'report', id: j.report_id })}>Measurements</a>}
                    {j.estimate_id && <a href={href({ page: 'estimate', id: j.estimate_id })}>Estimate</a>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </>
  )
}
