import React from 'react'
import ReactDOM from 'react-dom/client'
import './styles.css'

const models = [
  { name: 'SpamGuard-v1', status: 'HEALTHY', health: '92.3', action: 'CONTINUE_MONITORING' },
  { name: 'MarketingFilter', status: 'WARNING', health: '66.7', action: 'HUMAN_REVIEW' },
  { name: 'FraudTextGuard', status: 'CRITICAL', health: '48.2', action: 'RETRAIN' },
]

function App() {
  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">MLOps decision support</p>
          <h1>PhoenixML</h1>
        </div>
        <button className="primary-btn">New Evaluation</button>
      </header>

      <section className="metrics-grid">
        <div className="metric-box">
          <span>Total Models</span>
          <strong>24</strong>
        </div>
        <div className="metric-box warning">
          <span>Warning</span>
          <strong>3</strong>
        </div>
        <div className="metric-box critical">
          <span>Critical</span>
          <strong>1</strong>
        </div>
        <div className="metric-box safe">
          <span>Healthy</span>
          <strong>20</strong>
        </div>
      </section>

      <section className="panel">
        <h2>Model health overview</h2>
        <table>
          <thead>
            <tr>
              <th>Model</th>
              <th>Status</th>
              <th>Health</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {models.map((model) => (
              <tr key={model.name}>
                <td>{model.name}</td>
                <td>
                  <span className={`badge ${model.status.toLowerCase()}`}>{model.status}</span>
                </td>
                <td>{model.health}/100</td>
                <td>{model.action}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  )
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
