import { useEffect, useState, type ReactNode } from 'react'
import type { Source } from '../api'

export function Stepper({ step }: { step: 1 | 2 | 3 }) {
  const steps = ['Upload report', 'Review measurements', 'Estimate']
  return (
    <ol className="stepper">
      {steps.map((label, i) => (
        <li key={label} className={i + 1 === step ? 'current' : i + 1 < step ? 'done' : ''}>
          <span className="dot">{i + 1 < step ? '✓' : i + 1}</span>
          {label}
        </li>
      ))}
    </ol>
  )
}

const SOURCE_LABEL: Record<Source, string> = {
  template: 'Template',
  generic: 'Generic match',
  ai: 'AI read',
  manual: 'Edited',
  missing: 'Missing',
}

export function SourceBadge({ source, confidence, confirmed }: { source: Source; confidence: number; confirmed: boolean }) {
  const pct = source === 'missing' || source === 'manual' ? '' : ` · ${Math.round(confidence * 100)}%`
  return (
    <span className={`badge src-${source}`} title={confirmed ? 'Confirmed by a reviewer' : undefined}>
      {SOURCE_LABEL[source]}
      {pct}
      {confirmed && source !== 'manual' ? ' ✓' : ''}
    </span>
  )
}

export function StatusPill({ status }: { status: 'pass' | 'warn' | 'fail' | null }) {
  if (!status) return null
  const text = { pass: 'Verified', warn: 'Needs review', fail: 'Blocked' }[status]
  return <span className={`pill pill-${status}`}>{text}</span>
}

/** Number input that only reports a change on blur / Enter, so typing doesn't spam the API. */
export function CommitInput({
  value,
  onCommit,
  step = 'any',
  className = '',
  suffix,
  ariaLabel,
}: {
  value: number | null
  onCommit: (v: number | null) => void
  step?: string
  className?: string
  suffix?: ReactNode
  ariaLabel?: string
}) {
  const [text, setText] = useState(value === null ? '' : String(value))
  useEffect(() => setText(value === null ? '' : String(value)), [value])
  const commit = () => {
    const next = text.trim() === '' ? null : Number(text)
    if (next !== null && Number.isNaN(next)) {
      setText(value === null ? '' : String(value))
      return
    }
    if (next !== value) onCommit(next)
  }
  return (
    <span className={`commit-input ${className}`}>
      <input
        type="number"
        step={step}
        value={text}
        aria-label={ariaLabel}
        onChange={(e) => setText(e.target.value)}
        onBlur={commit}
        onKeyDown={(e) => e.key === 'Enter' && (e.target as HTMLInputElement).blur()}
      />
      {suffix && <span className="suffix">{suffix}</span>}
    </span>
  )
}

export function ErrorBanner({ error }: { error: string | null }) {
  if (!error) return null
  return <div className="banner banner-error">{error}</div>
}
