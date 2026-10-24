import { useEffect, useState } from 'react'
import { api, type PriceBook } from '../api'
import { CommitInput, ErrorBanner } from '../components/ui'

export default function PriceBookPage() {
  const [book, setBook] = useState<PriceBook | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [saved, setSaved] = useState<string | null>(null)

  const load = () => api.pricebook().then(setBook).catch((e) => setError(e.message))
  useEffect(() => {
    load()
  }, [])

  const save = (label: string, p: Promise<unknown>) =>
    p.then(() => {
      setSaved(`Saved ${label}. New estimates will use this price.`)
      load()
    }).catch((e) => setError(e.message))

  if (!book) return error ? <ErrorBanner error={error} /> : <p className="muted">Loading…</p>

  return (
    <>
      <div className="page-head">
        <div>
          <h1>Price book</h1>
          <p className="muted">Material prices, coverage formulas and labor rates every estimate is calculated from.</p>
        </div>
      </div>
      <ErrorBanner error={error} />
      {saved && <div className="banner banner-ok">{saved}</div>}

      <section className="card">
        <h2>Assemblies</h2>
        <div className="assemblies">
          {book.assemblies.map((a) => (
            <div key={a.code} className="assembly">
              <strong>{a.name}</strong>
              <p className="muted small">{a.description}</p>
              <p className="small">
                {a.material_skus.length} materials · {a.labor_codes.length} labor/other items
              </p>
            </div>
          ))}
        </div>
      </section>

      <section className="card">
        <h2>Materials</h2>
        <table className="table">
          <thead>
            <tr>
              <th>Material</th>
              <th>Quantity formula</th>
              <th>Coverage</th>
              <th>Waste</th>
              <th className="num">Price</th>
            </tr>
          </thead>
          <tbody>
            {book.materials.map((m) => (
              <tr key={m.sku}>
                <td>
                  {m.name}
                  <div className="muted small">
                    {m.sku} · {m.category}
                    {m.spec ? ` · ${m.spec}` : ''}
                  </div>
                </td>
                <td>
                  <code>{m.basis}</code>
                </td>
                <td className="small">{m.coverage}</td>
                <td className="small">{m.waste === 'job' ? 'Job waste %' : `${m.waste}%`}</td>
                <td className="num">
                  <CommitInput value={m.price} suffix={`/ ${m.unit}`} onCommit={(v) => v !== null && save(m.name, api.updateMaterialPrice(m.sku, v))} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section className="card">
        <h2>Labor & other rates</h2>
        <table className="table">
          <thead>
            <tr>
              <th>Item</th>
              <th>Quantity formula</th>
              <th className="num">Rate</th>
            </tr>
          </thead>
          <tbody>
            {book.labor.map((r) => (
              <tr key={r.code}>
                <td>
                  {r.name}
                  <div className="muted small">
                    {r.code} · {r.kind}
                  </div>
                </td>
                <td>
                  <code>{r.basis}</code>
                </td>
                <td className="num">
                  <CommitInput value={r.price} suffix={`/ ${r.unit}`} onCommit={(v) => v !== null && save(r.name, api.updateLaborRate(r.code, v))} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </>
  )
}
