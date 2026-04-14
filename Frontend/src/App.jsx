import RateTable from './components/RateTable'
import './App.css'

export default function App() {
  return (
    <div className="app">
      <header className="app-header">
        <span className="app-logo">Rate Tracker</span>
        <span className="app-tagline">Live interest rate dashboard</span>
      </header>
      <main className="app-main">
        <RateTable />
      </main>
      <footer className="app-footer">
        Rate Tracker &copy; {new Date().getFullYear()}
      </footer>
    </div>
  )
}
