export type Source = 'template' | 'generic' | 'ai' | 'manual' | 'missing'

export interface Measurement {
  key: string
  label: string
  unit: string
  required: boolean
  value: number | null
  original_value: number | null
  source: Source
  confidence: number
  evidence: string | null
  confirmed: boolean
}

export interface Issue {
  level: 'error' | 'warning'
  field: string | null
  message: string
}

export interface PitchArea {
  pitch: number
  area_sqft: number
}

export interface Report {
  id: number
  job_id: number
  job_name: string
  filename: string
  provider: string
  provider_name: string
  extraction_method: string
  uploaded_at: string
  notes: string[]
  pitch_breakdown: PitchArea[]
  measurements: Measurement[]
  verification: { status: 'pass' | 'warn' | 'fail'; can_estimate: boolean; issues: Issue[] }
  estimate_ids: number[]
}

export interface LineItem {
  id: number
  kind: 'material' | 'labor' | 'other'
  ref_code: string
  description: string
  unit: string
  calc_qty: number
  qty: number
  unit_cost: number
  total: number
  formula: string
  overridden: boolean
}

export interface Totals {
  materials: number
  material_tax: number
  labor: number
  other: number
  total_cost: number
  selling_price: number
  gross_profit: number
  actual_margin_pct: number
  price_per_square: number
}

export interface Estimate {
  id: number
  job_id: number
  job_name: string
  report_id: number
  assembly_code: string
  assembly_name: string
  waste_pct: number
  margin_pct: number
  tax_pct: number
  created_at: string
  items: LineItem[]
  totals: Totals
}

export interface JobRow {
  id: number
  name: string
  created_at: string
  report_id: number | null
  provider_name: string | null
  status: 'pass' | 'warn' | 'fail' | null
  estimate_id: number | null
  selling_price: number | null
}

export interface Assembly {
  code: string
  name: string
  description: string
  material_skus: string[]
  labor_codes: string[]
}

export interface PriceBook {
  materials: { sku: string; name: string; category: string; unit: string; price: number; basis: string; coverage: string; waste: string; spec: string | null }[]
  labor: { code: string; kind: string; name: string; unit: string; price: number; basis: string }[]
  assemblies: Assembly[]
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`/api${path}`, init)
  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`
    try {
      const body = await res.json()
      if (typeof body.detail === 'string') detail = body.detail
    } catch {
      /* not JSON */
    }
    throw new Error(detail)
  }
  return res.json() as Promise<T>
}

const json = (method: string, body: unknown): RequestInit => ({
  method,
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(body),
})

export const api = {
  health: () => request<{ ai_enabled: boolean; providers: { key: string; name: string }[] }>('/health'),
  samples: () => request<{ name: string; size: number }[]>('/samples'),
  jobs: () => request<JobRow[]>('/jobs'),
  upload: (file: File, jobName: string, useAi: boolean) => {
    const form = new FormData()
    form.append('file', file)
    if (jobName) form.append('job_name', jobName)
    form.append('use_ai', String(useAi))
    return request<Report>('/reports', { method: 'POST', body: form })
  },
  loadSample: (name: string) => request<Report>(`/samples/${encodeURIComponent(name)}/load`, { method: 'POST' }),
  report: (id: number) => request<Report>(`/reports/${id}`),
  updateMeasurements: (id: number, body: { values?: Record<string, number | null>; confirm?: string[]; pitch_breakdown?: PitchArea[] }) =>
    request<Report>(`/reports/${id}/measurements`, json('PATCH', body)),
  createEstimate: (reportId: number, assembly_code: string) =>
    request<Estimate>(`/reports/${reportId}/estimates`, json('POST', { assembly_code })),
  estimate: (id: number) => request<Estimate>(`/estimates/${id}`),
  updateEstimate: (id: number, body: Partial<Pick<Estimate, 'waste_pct' | 'margin_pct' | 'tax_pct'>>) =>
    request<Estimate>(`/estimates/${id}`, json('PATCH', body)),
  updateLineItem: (id: number, body: { qty?: number; unit_cost?: number; reset?: boolean }) =>
    request<Estimate>(`/line-items/${id}`, json('PATCH', body)),
  pricebook: () => request<PriceBook>('/pricebook'),
  updateMaterialPrice: (sku: string, price: number) => request(`/pricebook/materials/${sku}`, json('PATCH', { price })),
  updateLaborRate: (code: string, price: number) => request(`/pricebook/labor/${code}`, json('PATCH', { price })),
}

export const money = (n: number, cents = true) =>
  n.toLocaleString('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: cents ? 2 : 0, maximumFractionDigits: cents ? 2 : 0 })

export const num = (n: number | null, max = 2) => (n === null ? '' : n.toLocaleString('en-US', { maximumFractionDigits: max }))
