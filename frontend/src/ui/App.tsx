
import React, { useEffect, useState } from "react"

const API = (import.meta as any).env.VITE_API_BASE || "http://localhost:8000"

function useUsers() {
  const [users, setUsers] = useState<any[]>([])
  useEffect(() => {
    fetch(`${API}/users`).then(r => r.json()).then(setUsers).catch(()=>{})
  }, [])
  return users
}

export function App() {
  const users = useUsers()
  return (
    <div style={{fontFamily:"system-ui", margin:"2rem"}}>
      <h1>NCHD Rostering & Leave System</h1>
      <p>Demo UI — role dashboards forthcoming.</p>
      <section>
        <h2>Users</h2>
        <ul>
          {users.map(u => <li key={u.id}>{u.name} — {u.role}</li>)}
        </ul>
      </section>
    </div>
  )
}
