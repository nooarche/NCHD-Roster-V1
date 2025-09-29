import React, { useEffect, useState } from "react"
const API = (import.meta as any).env?.VITE_API_BASE || "/api"

type Issue = { user_id:number; user_name:string; slot_id:number; message:string }
type Report = { ok:boolean; issues: Issue[] }

export default function ValidationCard({year, month}:{year:number; month:number}) {
  const [report, setReport] = useState<Report|null>(null)
  const [loading, setLoading] = useState(false)
  const [open, setOpen] = useState(false)

  async function runValidation() {
    setLoading(true)
    try {
      const r = await fetch(`${API}/validate/rota?year=${year}&month=${month}`)
      const data = await r.json()
      setReport(data)
      setOpen(true)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{border:"1px solid #eee", borderRadius:6, padding:10, display:"flex", alignItems:"center", gap:10}}>
      <strong>Validation</strong>
      <button onClick={runValidation} disabled={loading}>{loading ? "Running…" : "Validate month"}</button>
      {report && <span style={{marginLeft:"auto", fontSize:12, color: report.ok ? "#0a0" : "#b00"}}>
        {report.ok ? "OK: no issues" : `${report.issues.length} issue(s)`}
      </span>}

      {/* Drawer-style details */}
      {open && report && (
        <div style={{position:"fixed", inset:0, background:"rgba(0,0,0,0.35)", display:"flex", alignItems:"center", justifyContent:"center"}}>
          <div style={{background:"white", width:720, maxHeight:"80vh", overflow:"auto", padding:16, borderRadius:8}}>
            <div style={{display:"flex", alignItems:"center"}}>
              <h3 style={{margin:0}}>Validation report — {year}-{String(month).padStart(2,"0")}</h3>
              <button onClick={()=>setOpen(false)} style={{marginLeft:"auto"}}>Close</button>
            </div>
            {report.issues.length === 0 ? (
              <p style={{color:"#0a0"}}>No issues found 🎉</p>
            ) : (
              <table style={{borderCollapse:"collapse", width:"100%", marginTop:10}}>
                <thead>
                  <tr>
                    <th style={{textAlign:"left"}}>User</th>
                    <th style={{textAlign:"left"}}>Slot ID</th>
                    <th style={{textAlign:"left"}}>Message</th>
                  </tr>
                </thead>
                <tbody>
                {report.issues.map((i, idx)=>(
                  <tr key={idx}>
                    <td>{i.user_name} <span style={{color:"#777"}}>#{i.user_id}</span></td>
                    <td>{i.slot_id || "—"}</td>
                    <td>{i.message}</td>
                  </tr>
                ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
