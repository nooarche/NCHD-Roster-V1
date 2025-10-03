import React, { useState } from "react"

type Props = { apiBase: string }

export default function RosterEditor({ apiBase }: Props) {
  const [year, setYear] = useState<number>(new Date().getFullYear())
  const [month, setMonth] = useState<number>(new Date().getMonth() + 1)
  const [freeze, setFreeze] = useState<string>("") // e.g. 2026-02-01
  const [status, setStatus] = useState<string>("")

  const runAutofill = async () => {
    setStatus("Running…")
    try {
      const payload: any = { year, month, night_calls_per_day: 1 }
      if (freeze) payload.freeze_before = freeze
      const r = await fetch(`${apiBase}/oncall/autofill`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify(payload)
      })
      const text = await r.text()
      setStatus(`${r.status} ${r.statusText}: ${text}`)
    } catch (e:any) {
      setStatus(`Error: ${e.message}`)
    }
  }

  return (
    <section style={{display:"grid",gap:"8px",maxWidth:480}}>
      <h2>Roster · Autofill</h2>
      <label>Year<br/><input type="number" value={year} onChange={e=>setYear(parseInt(e.target.value||"0"))}/></label>
      <label>Month (1–12)<br/><input type="number" value={month} onChange={e=>setMonth(parseInt(e.target.value||"0"))}/></label>
      <label>Freeze all dates before (YYYY-MM-DD)<br/><input value={freeze} onChange={e=>setFreeze(e.target.value)} placeholder="2026-02-01"/></label>
      <button onClick={runAutofill}>Autofill nights</button>
      {status && <pre style={{whiteSpace:"pre-wrap",background:"#f7f7f7",padding:"6px"}}>{status}</pre>}
    </section>
  )
}
