import { Fragment, useEffect, useState } from 'react'
import { api, money, num, type Estimate, type LineItem } from '../api'
import { CommitInput, ErrorBanner, Stepper } from '../components/ui'
import { href } from '../router'

const SECTIONS: { kind: LineItem['kind']; title: string }[] = [
  { kind: 'material', title: 'Materials' },
  { kind: 'labor', title: 'Labor' },
  { kind: 'other', title: 'Other costs' },
]

export default function EstimatePage({ id }: { id: number }) {
  const [est, setEst] = useState<Estimate | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [open, setOpen] = useState<number | null>(null)

  useEffect(() => {
    api.estimate(id).then(setEst).catch((e) => setError(e.message))
  }, [id])

  const apply = (p: Promise<Estimate>) =>
    p.then((e) => {
      setEst(e)
      setError(null)
    }).catch((e) => setError(e.message))

  if (!est) return error ? <ErrorBanner error={error} /> : <p className="muted">Loading…</p>
  const t = est.totals

  return (
    <>
      <div className="no-print">
        <Stepper step={3} />
      </div>
      <div className="page-head">
        <div>
          <h1>{est.job_name}</h1>
          <p className="muted">
            Estimate #{est.id} · {est.assembly_name} · {new Date(est.created_at).toLocaleDateString()}
          </p>
        </div>
        <div className="row-gap no-print">
          <a className="btn btn-ghost" href={href({ page: 'report', id: est.report_id })}>
            Back to measurements
          </a>
          <button className="btn" onClick={() => window.print()}>
            Print / PDF
          </button>
        </div>
      </div>
      <ErrorBanner error={error} />

      <div className="estimate-layout">
        <div>
          <section className="card controls no-print">
            <label className="field inline">
              <span>Waste</span>
              <CommitInput value={est.waste_pct} suffix="%" onCommit={(v) => v !== null && apply(api.updateEstimate(est.id, { waste_pct: v }))} />
            </label>
            <label className="field inline">
              <span>Target margin</span>
              <CommitInput value={est.margin_pct} suffix="%" onCommit={(v) => v !== null && apply(api.updateEstimate(est.id, { margin_pct: v }))} />
            </label>
            <label className="field inline">
              <span>Material tax</span>
              <CommitInput value={est.tax_pct} suffix="%" onCommit={(v) => v !== null && apply(api.updateEstimate(est.id, { tax_pct: v }))} />
            </label>
            <p className="muted small">Changing waste re-runs the material formulas. Quantities you edited by hand are kept.</p>
          </section>

          {SECTIONS.map(({ kind, title }) => {
            const items = est.items.filter((i) => i.kind === kind)
            if (!items.length) return null
            const subtotal = items.reduce((s, i) => s + i.total, 0)
            return (
              <section className="card" key={kind}>
                <div className="card-head">
                  <h2>{title}</h2>
                  {kind === 'material' && <span className="muted small no-print">Click an item to see how its quantity was calculated.</span>}
                </div>
                <table className="table items">
                  <thead>
                    <tr>
                      <th>Item</th>
                      <th className="num">Qty</th>
                      <th>Unit</th>
                      <th className="num">Unit price</th>
                      <th className="num">Total</th>
                    </tr>
                  </thead>
                  <tbody>
                    {items.map((i) => (
                      <Fragment key={i.id}>
                        <tr className={i.overridden ? 'overridden' : ''}>
                          <td>
                            <button className="link item-name" onClick={() => setOpen(open === i.id ? null : i.id)} title="Show calculation">
                              {i.description}
                            </button>
                            {i.overridden && (
                              <span className="badge src-manual">
                                Edited ·{' '}
                                <button className="link" onClick={() => apply(api.updateLineItem(i.id, { reset: true }))}>
                                  reset
                                </button>
                              </span>
                            )}
                          </td>
                          <td className="num">
                            <CommitInput value={i.qty} ariaLabel={`${i.description} quantity`} onCommit={(v) => v !== null && apply(api.updateLineItem(i.id, { qty: v }))} />
                          </td>
                          <td>{i.unit}</td>
                          <td className="num">
                            <CommitInput value={i.unit_cost} ariaLabel={`${i.description} unit cost`} suffix={`/ ${i.unit}`} onCommit={(v) => v !== null && apply(api.updateLineItem(i.id, { unit_cost: v }))} />
                          </td>
                          <td className="num strong">{money(i.total)}</td>
                        </tr>
                        {open === i.id && (
                          <tr className="formula-row">
                            <td colSpan={5}>
                              <code>{i.formula}</code>
                              {i.overridden && i.qty !== i.calc_qty && <span className="muted small"> · formula qty {num(i.calc_qty)}</span>}
                            </td>
                          </tr>
                        )}
                      </Fragment>
                    ))}
                  </tbody>
                  <tfoot>
                    <tr>
                      <td colSpan={4}>{title} subtotal</td>
                      <td className="num strong">{money(subtotal)}</td>
                    </tr>
                  </tfoot>
                </table>
              </section>
            )
          })}
        </div>

        <aside className="card summary">
          <h2>Summary</h2>
          <dl>
            <dt>Materials</dt>
            <dd>{money(t.materials)}</dd>
            <dt>Material tax ({est.tax_pct}%)</dt>
            <dd>{money(t.material_tax)}</dd>
            <dt>Labor</dt>
            <dd>{money(t.labor)}</dd>
            <dt>Other</dt>
            <dd>{money(t.other)}</dd>
            <dt className="sep">Total cost</dt>
            <dd className="sep strong">{money(t.total_cost)}</dd>
          </dl>
          <div className="price">
            <span className="muted small">Recommended selling price</span>
            <strong>{money(t.selling_price, false)}</strong>
            <span className="muted small">{money(t.price_per_square)} per square</span>
          </div>
          <dl>
            <dt>Gross profit</dt>
            <dd className="good">{money(t.gross_profit)}</dd>
            <dt>Margin</dt>
            <dd>{t.actual_margin_pct.toFixed(1)}%</dd>
          </dl>
          <p className="muted small">Price = cost ÷ (1 − {est.margin_pct}% margin), rounded up to the next $10.</p>
        </aside>
      </div>
    </>
  )
}
