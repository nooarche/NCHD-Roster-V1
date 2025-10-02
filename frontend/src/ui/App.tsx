// frontend/src/ui/App.tsx
import React, { useEffect, useState } from "react"
import AdminPostBuilder from "./admin/AdminPostBuilder"

const API_BASE = (import.meta as any).env?.VITE_API_BASE || "http://localhost:8000"

type User = { id: number, name: string, role: string }

function useUsers() {
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const refresh = async () => {
    setLoading(true); setError(null)
    try {
      const r = await fetch(`${API_BASE}/users`)
      setUsers(await r.json())
    } catch (e: any) {
      setError(e?.message ?? String(e))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { refresh() }, [])
  return { users, loading, error, refresh }
}

export function App() {
  const { users, loading, error } = useUsers()
  const [tab, setTab] = useState<"Admin"|"Supervisor"|"NCHD"|"Staff">("Admin")

  return (
    <div style={{fontFamily:"system-ui", margin:"2rem", display:"grid", gap:"1.25rem"}}>
      <header style={{display:"flex", justifyContent:"space-between", alignItems:"center"}}>
        <h1>NCHD Rostering & Leave System</h1>
        <nav style={{display:"flex", gap:"0.5rem"}}>
          {(["Admin","Supervisor","NCHD","Staff"] as const).map(t => (
            <button key={t} onClick={()=>setTab(t)} disabled={tab===t}>{t}</button>
          ))}
        </nav>
      </header>

      {tab === "Admin" && (
        <AdminPostBuilder apiBase={API_BASE} />
      )}

      {tab !== "Admin" && (
        <section>
          <h2>{tab} View (placeholder)</h2>
          <p>Coming soon.</p>
        </section>
      )}

      <section>
        <h2>Users</h2>
        {loading && <div>Loading users…</div>}
        {error && <div style={{color:"crimson"}}>Error: {error}</div>}
        <ul>
          {users.map(u => <li key={u.id}>{u.name} — {u.role}</li>)}
        </ul>
      </section>
    </div>
  )
}
