import React, { useEffect, useState } from "react";

function App() {
  const [signals, setSignals] = useState([]);

  useEffect(() => {
    async function fetchSignals() {
      try {
        // Ideally, host this JSON via backend or GitHub Pages
        const res = await fetch("/signals.json");
        const data = await res.json();
        setSignals(data);
      } catch (err) {
        console.error("Error loading signals", err);
      }
    }
    fetchSignals();
  }, []);

  return (
    <div className="dashboard" style={{ padding: "1rem", fontFamily: "sans-serif" }}>
      <h1>Crypto Signal Dashboard</h1>
      <button onClick={() => window.location.reload()} style={{ marginBottom: "1rem" }}>
        Scan Now
      </button>
      <div className="signal-list" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill,minmax(320px,1fr))', gap: '1rem' }}>
        {signals.length === 0 && <p>No signals yet</p>}
        {signals.map(signal => (
          <div key={signal.ticker} style={{ border: "1px solid #ccc", borderRadius: 8, padding: "1rem", background: "#f9f9f9" }}>
            <h2>{signal.ticker} <small>{signal.ai_score}/100</small></h2>
            <p>Price: ${signal.price.toFixed(2)}</p>
            <p>RSI: {signal.technicals.rsi}</p>
            <p>Mentions: {signal.sentiment.mentions}</p>
            <p>{signal.validation}</p>
            <p>
              TP: ${signal.risk_management.tp.toFixed(2)} | SL: ${signal.risk_management.sl.toFixed(2)}
            </p>
            <p>
              <a href={signal.links.chart} target="_blank" rel="noreferrer">Chart</a> |{" "}
              <a href={signal.links.news} target="_blank" rel="noreferrer">News</a> |{" "}
              <a href={signal.links.catalyst} target="_blank" rel="noreferrer">Catalyst</a>
            </p>
            <small>{signal.timestamp}</small>
          </div>
        ))}
      </div>
    </div>
  );
}

export default App;
