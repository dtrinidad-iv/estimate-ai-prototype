import { useEffect, useState } from 'react'

export type Route =
  | { page: 'home' }
  | { page: 'report'; id: number }
  | { page: 'estimate'; id: number }
  | { page: 'pricebook' }

function parse(hash: string): Route {
  const [, page, id] = hash.replace(/^#/, '').split('/')
  if (page === 'report' && id) return { page: 'report', id: Number(id) }
  if (page === 'estimate' && id) return { page: 'estimate', id: Number(id) }
  if (page === 'pricebook') return { page: 'pricebook' }
  return { page: 'home' }
}

export const href = (r: Route) => (r.page === 'home' ? '#/' : 'id' in r ? `#/${r.page}/${r.id}` : `#/${r.page}`)

export const navigate = (r: Route) => {
  window.location.hash = href(r)
}

export function useRoute(): Route {
  const [route, setRoute] = useState(() => parse(window.location.hash))
  useEffect(() => {
    const onChange = () => setRoute(parse(window.location.hash))
    window.addEventListener('hashchange', onChange)
    return () => window.removeEventListener('hashchange', onChange)
  }, [])
  return route
}
