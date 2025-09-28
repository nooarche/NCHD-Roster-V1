import React, { useEffect, useState } from "react"

type User = { id:number; name:string; email:string; role:string }

const API = (import.meta as any).env?.VITE_API_BASE || "http://localhost:8000"

function useUsers() {
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    (async () => {
      try {
        const res = await fetch(`${API}/users`)
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        const data = await res.json()
        setUsers(data)
      } catch (e:any) {
        setError(e.message || "Failed to load users")
      } finally {
        setLoading(false)
      }
    })()
  }, [])

  return { users, loading, error }
}

const TabButton: React.FC<{active:boolean; onClick:()=>void; children:React.ReactNode}> = ({active,onClick,children}) => (
  <button
    onClick={onClick}
    style={{
      padding:"0.5rem 1rem",
      marginRight:8,
      border:"1px solid #ddd",
      borderBottom: active ? "2px solid black" : "1px solid #ddd",
      background: active ? "#f8f8f8" : "white",
      cursor:"pointer", borderRadius:6
    }}
  >{children}</button>
)

const RoleBadge: React.FC<{role:string}> = ({role}) => (
  <span style={{
    padding:"2px 8px", borderRadius:999,
    border:"1px solid #ddd", fontSize:12,
    background: role==="admin" ? "#fff3cd" :
               role==="supervisor" ? "#e7f1ff" :
               role==="nchd" ? "#eafaf0" : "#eee"
  }}>{role.toUpperCase()}</span>
)

export function App() {
  const { users, loading, error } = useUsers()
  const [tab, setTab] = useState<"Admin"|"Supervisor"|"NCHD"|"Staff">("Admin")

  return (
    <div style={{fontFamily:"system-ui,-apple-system,Segoe UI,Roboto", margin:"2rem", lineHeight:1.35}}>
      <h1 style={{marginBottom:4}}>NCHD Rostering & Leave System</h1>
      <p style={{marginTop:0, color:"#555"}}>Demo UI — role dashboards forthcoming.</p>

      {/* Tabs */}
      <div style={{margin:"1rem 0"}}>
        {(["Admin","Supervisor","NCHD","Staff"] as const).map(t =>
          <TabButton key={t} active={t===tab} onClick={()=>setTab(t)}>{t}</TabButton>
        )}
      </div>

      {/* Users section */}
      <section>
        <h2 style={{marginBottom:8}}>Users {loading ? "" : `(${users.length})`}</h2>
        {loading && <div>Loading users…</div>}
        {error && <div style={{color:"crimson"}}>Error: {error}</div>}
        {!loading && !error && users.length === 0 && <div>No users yet.</div>}
        {!loading && !error && users.length > 0 && (
          <div style={{overflowX:"auto"}}>
            <table style={{borderCollapse:"collapse", minWidth:560}}>
              <thead>
                <tr>
                  <th style={th}>ID</th>
                  <th style={th}>Name</th>
                  <th style={th}>Email</th>
                  <th style={th}>Role</th>
                </tr>
              </thead>
              <tbody>
              {users.map(u => (
                <tr key={u.id}>
                  <td style={td}>{u.id}</td>
                  <td style={td}>{u.name}</td>
                  <td style={td}>{u.email}</td>
                  <td style={td}><RoleBadge role={u.role}/></td>
                </tr>
              ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {/* Placeholder per-role panels */}
      <section style={{marginTop:"2rem"}}>
        {tab === "Admin" && <div>Admin dashboard will show: EWTD (European Working Time Directive) / Contract compliance, OPD (Outpatient Department) Day Editor, alerts, audits.</div>}
        {tab === "Supervisor" && <div>Supervisor dashboard will show: team calendar, leave approvals, teaching/supervision quick actions.</div>}
        {tab === "NCHD" && <div>NCHD dashboard will show: personal calendar, Leave Helper, deviation log.</div>}
        {tab === "Staff" && <div>Staff dashboard will show: operational week view (on-call, OPD, base, leave), emergency contacts (audited).</div>}
      </section>
    </div>
  )
}

const th: React.CSSProperties = { textAlign:"left", borderBottom:"1px solid #ddd", padding:"8px 10px", fontWeight:600 }
const td: React.CSSProperties = { borderBottom:"1px solid #f0f0f0", padding:"8px 10px" }
