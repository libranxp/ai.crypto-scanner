import React, { useEffect, useState } from "react";

function App() {
  const [signals, setSignals] = useState([]);

  useEffect(() => {
    async function fetchSignals() {
      try {
        const res = await fetch("https://your-backend-domain.com/signals");
        const data = await res.json();
        setSignals(data);
      } catch (err) {
        console.error("Failed to load signals", err);
      }
    }
    fetchSignals();
  }, []);

  return (
    <div style={{ padding: 20, fontFamily: "Arial, sans-serif" }}>
      <h1>Crypto Signal Dashboard</h1>
      <button onClick={() => window.location.reload()} style={{ marginBottom: 20 }}>
        Scan Now
      </button>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 20 }}>
        {signals.length === 0 ? (
          <p>No signals currently.</p>
        ) : (
          signals.map(sig => (
            <div key={sig.ticker} style={{ border: "1px solid #ccc", borderRadius: 8, padding: 15, width: 320 }}>
              <h2>{sig.ticker} <small>({sig.ai_score}/100)</small></h2>
              <p>Price: ${sig.price.toFixed(2)}</p>
              <p>RSI: {sig.technicals.rsi}</p>
              <p>Mentions: {sig.sentiment.mentions}</p>
              <p>{sig.validation}</p>
              <p>TP: ${sig.risk_management.tp.toFixed(2)} | SL: ${sig.risk_management.sl.toFixed(2)}</p>
              <p>
                <a href={sig.links.chart} target="_blank" rel="noreferrer">Chart</a> |{" "}
                <a href={sig.links.news} target="_blank" rel="noreferrer">News</a> |{" "}
                <a href={sig.links.catalyst} target="_blank" rel="noreferrer">Catalyst</a>
              </p>
              <small>{sig.timestamp}</small>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

export default App;
