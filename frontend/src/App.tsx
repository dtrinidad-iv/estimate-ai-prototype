import { href, useRoute } from './router'
import HomePage from './pages/HomePage'
import ReviewPage from './pages/ReviewPage'
import EstimatePage from './pages/EstimatePage'
import PriceBookPage from './pages/PriceBookPage'

export default function App() {
  const route = useRoute()
  return (
    <>
      <header className="topbar no-print">
        <a className="brand" href={href({ page: 'home' })}>
          <svg viewBox="0 0 32 32" width="26" height="26" aria-hidden>
            <rect width="32" height="32" rx="7" fill="var(--accent)" />
            <path d="M6 18 16 9l10 9v7H6z" fill="white" />
          </svg>
          EstimateAI
        </a>
        <nav>
          <a className={route.page !== 'pricebook' ? 'active' : ''} href={href({ page: 'home' })}>
            Estimates
          </a>
          <a className={route.page === 'pricebook' ? 'active' : ''} href={href({ page: 'pricebook' })}>
            Price book
          </a>
        </nav>
      </header>
      <main className="container">
        {route.page === 'home' && <HomePage />}
        {route.page === 'report' && <ReviewPage key={route.id} id={route.id} />}
        {route.page === 'estimate' && <EstimatePage key={route.id} id={route.id} />}
        {route.page === 'pricebook' && <PriceBookPage />}
      </main>
    </>
  )
}
