import { useEffect, useMemo, useState } from 'react'
import { api, num, type Assembly, type PitchArea, type Report } from '../api'
import { CommitInput, ErrorBanner, SourceBadge, StatusPill, Stepper } from '../components/ui'
import { href, navigate } from '../router'

export default function ReviewPage({ id }: { id: number }) {
  const [report, setReport] = useState<Report | null>(null)
  const [assemblies, setAssemblies] = useState<Assembly[]>([])
  const [assembly, setAssembly] = useState('ARCH-STD')
  const [draft, setDraft] = useState<Record<string, number | null>>({})
  const [breakdown, setBreakdown] = useState<PitchArea[] | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api.report(id).then(setReport).catch((e) => setError(e.message))
    api.pricebook().then((p) => setAssemblies(p.assemblies)).catch(() => {})
  }, [id])

  const issuesByField = useMemo(() => {
    const map: Record<string, 'error' | 'warning'> = {}
    for (const i of report?.verification.issues ?? []) {
      if (i.field && map[i.field] !== 'error') map[i.field] = i.level
    }
    return map
  }, [report])

  if (!report) return error ? <ErrorBanner error={error} /> : <p className="muted">Loading…</p>

  const dirty = Object.keys(draft).length > 0 || breakdown !== null
  const rows = breakdown ?? report.pitch_breakdown
  const flagged = report.measurements.filter((m) => m.value !== null && !m.confirmed && m.source !== 'manual' && m.confidence < 0.9)
  const breakdownTotal = rows.reduce((s, r) => s + (r.area_sqft || 0), 0)

  const save = async (extra?: { confirm?: string[] }) => {
    setBusy(true)
    setError(null)
    try {
      const updated = await api.updateMeasurements(report.id, {
        values: draft,
        confirm: extra?.confirm ?? [],
        ...(breakdown ? { pitch_breakdown: breakdown.filter((r) => r.area_sqft > 0) } : {}),
      })
      setReport(updated)
      setDraft({})
      setBreakdown(null)
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setBusy(false)
    }
  }

  const generate = async () => {
    setBusy(true)
    setError(null)
    try {
      const est = await api.createEstimate(report.id, assembly)
      navigate({ page: 'estimate', id: est.id })
    } catch (e) {
      setError((e as Error).message)
      setBusy(false)
    }
  }

  const editRow = (i: number, patch: Partial<PitchArea>) =>
    setBreakdown(rows.map((r, j) => (j === i ? { ...r, ...patch } : r)))

  const v = report.verification
  return (
    <>
      <Stepper step={2} />
      <div className="page-head">
        <div>
          <h1>{report.job_name}</h1>
          <p className="muted">
            {report.filename} · {report.provider_name} · extracted by <code>{report.extraction_method}</code>
          </p>
        </div>
        <StatusPill status={v.status} />
      </div>
      <ErrorBanner error={error} />

      <div className="review-layout">
        <div className="review-main">
          <section className={`card verify verify-${v.status}`}>
            <h2>
              {v.status === 'pass' && 'All checks passed'}
              {v.status === 'warn' && `${v.issues.length} item${v.issues.length > 1 ? 's' : ''} to review`}
              {v.status === 'fail' && 'Fix these before estimating'}
            </h2>
            {v.issues.length > 0 && (
              <ul className="issues">
                {v.issues.map((i, n) => (
                  <li key={n} className={`issue-${i.level}`}>
                    <span className="issue-level">{i.level === 'error' ? 'Error' : 'Check'}</span>
                    {i.message}
                  </li>
                ))}
              </ul>
            )}
            {report.notes.length > 0 && (
              <ul className="notes">
                {report.notes.map((n, i) => (
                  <li key={i}>{n}</li>
                ))}
              </ul>
            )}
          </section>

          <section className="card">
            <div className="card-head">
              <h2>Measurements</h2>
              <div className="row-gap">
                {flagged.length > 0 && (
                  <button className="btn btn-ghost" disabled={busy || dirty} onClick={() => save({ confirm: flagged.map((m) => m.key) })}>
                    Confirm {flagged.length} flagged value{flagged.length > 1 ? 's' : ''}
                  </button>
                )}
                <button className="btn" disabled={!dirty || busy} onClick={() => save()}>
                  Save changes
                </button>
              </div>
            </div>
            <table className="table measurements">
              <thead>
                <tr>
                  <th>Measurement</th>
                  <th>Value</th>
                  <th>Source</th>
                  <th>From the PDF</th>
                </tr>
              </thead>
              <tbody>
                {report.measurements.map((m) => {
                  const value = m.key in draft ? draft[m.key] : m.value
                  const changed = m.key in draft
                  return (
                    <tr key={m.key} className={issuesByField[m.key] ? `row-${issuesByField[m.key]}` : ''}>
                      <td>
                        {m.label}
                        {m.required && <span className="req" title="Required">*</span>}
                      </td>
                      <td>
                        <CommitInput
                          value={value}
                          ariaLabel={m.label}
                          className={changed ? 'changed' : ''}
                          suffix={m.unit}
                          onCommit={(next) => setDraft((d) => ({ ...d, [m.key]: next }))}
                        />
                      </td>
                      <td>
                        <SourceBadge source={changed ? 'manual' : m.source} confidence={m.confidence} confirmed={m.confirmed} />
                      </td>
                      <td className="evidence">
                        {m.evidence ?? <span className="muted">—</span>}
                        {m.source === 'manual' && m.original_value !== null && m.original_value !== m.value && (
                          <span className="muted small"> (was {num(m.original_value)})</span>
                        )}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </section>

          <section className={`card ${issuesByField['pitch_breakdown'] ? `card-${issuesByField['pitch_breakdown']}` : ''}`}>
            <div className="card-head">
              <h2>Area by pitch</h2>
              <button className="btn btn-ghost" onClick={() => setBreakdown([...rows, { pitch: 6, area_sqft: 0 }])}>
                Add row
              </button>
            </div>
            <p className="muted small">Used for steep-slope labor charges. If empty, the whole roof is priced at the predominant pitch.</p>
            <table className="table compact">
              <thead>
                <tr>
                  <th>Pitch</th>
                  <th>Area</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {rows.map((r, i) => (
                  <tr key={i}>
                    <td>
                      <CommitInput value={r.pitch} suffix="/12" onCommit={(p) => editRow(i, { pitch: p ?? 0 })} />
                    </td>
                    <td>
                      <CommitInput value={r.area_sqft} suffix="sq ft" onCommit={(a) => editRow(i, { area_sqft: a ?? 0 })} />
                    </td>
                    <td>
                      <button className="link" onClick={() => setBreakdown(rows.filter((_, j) => j !== i))}>
                        Remove
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr>
                  <td>Total</td>
                  <td>{num(breakdownTotal, 0)} sq ft</td>
                  <td />
                </tr>
              </tfoot>
            </table>
          </section>

          <section className="card generate">
            <label className="field">
              <span>Assembly</span>
              <select value={assembly} onChange={(e) => setAssembly(e.target.value)}>
                {assemblies.map((a) => (
                  <option key={a.code} value={a.code}>
                    {a.name}
                  </option>
                ))}
              </select>
            </label>
            <p className="muted small">{assemblies.find((a) => a.code === assembly)?.description}</p>
            <div className="row-gap">
              <button className="btn btn-primary" disabled={!v.can_estimate || dirty || busy} onClick={generate}>
                Generate estimate
              </button>
              {dirty && <span className="muted small">Save your changes first.</span>}
              {!v.can_estimate && !dirty && <span className="muted small">Resolve the errors above to continue.</span>}
              {report.estimate_ids.map((eid) => (
                <a key={eid} href={href({ page: 'estimate', id: eid })}>
                  Estimate #{eid}
                </a>
              ))}
            </div>
          </section>
        </div>

        <aside className="review-pdf">
          <iframe title="Measurement report" src={`/api/reports/${report.id}/pdf#view=FitH`} />
        </aside>
      </div>
    </>
  )
}
