// frontend/src/ui/App.tsx
import React, { useEffect, useState } from "react"
import AdminPostBuilder from "./admin/AdminPostBuilder"
import RosterEditor from "./RosterEditor"


const API_BASE = (import.meta as any).env?.VITE_API_BASE || "/api";

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
  const [tab, setTab] = useState<"Admin"|"Supervisor"|"NCHD"|"Staff"|"Roster">("Admin")
  // ...
  return (
    <>
      <nav style={{display:"flex",gap:8,marginBottom:12}}>
        <button onClick={()=>setTab("Admin")}>Admin</button>
        <button onClick={()=>setTab("Roster")}>Roster</button>
        {/* …other tabs */}
      </nav>

      {tab==="Admin"  && <AdminPostBuilder apiBase={API_BASE}/>}
      {tab==="Roster" && <RosterEditor apiBase={API_BASE}/>}
    </>
  )
}

