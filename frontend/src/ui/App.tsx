import React, { useEffect, useMemo, useState } from "react"

type Role = "admin" | "supervisor" | "nchd" | "staff"
type User = { id:number; name:string; email:string; role:Role }

const API = (import.meta as any).env?.VITE_API_BASE || "/api"

function useUsers() {
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  async function refresh() {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`${API}/users`)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      setUsers(await res.json())
    } catch (e:any) {
      setError(e.message || "Failed to load users")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { refresh() }, [])
  return { users, setUsers, loading, error, refresh }
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

const RoleBadge: React.FC<{role:Role}> = ({role}) => (
  <span style={{
    padding:"2px 8px", borderRadius:999,
    border:"1px solid #ddd", fontSize:12,
    background: role==="admin" ? "#fff3cd" :
               role==="supervisor" ? "#e7f1ff" :
               role==="nchd" ? "#eafaf0" : "#eee"
  }}>{role.toUpperCase()}</span>
)

function UsersTable({users}:{users:User[]}) {
  return (
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
          {users.map(u=>(
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
  )
}

/** ADMIN: Users CRUD panel */
function AdminUsers({users, refresh}:{users:User[], refresh:()=>void}) {
  const [form, setForm] = useState<{name:string; email:string; role:Role}>({name:"", email:"", role:"nchd"})
  const [saving, setSaving] = useState(false)
  const [err, setErr] = useState<string|null>(null)
  const [editing, setEditing] = useState<number|null>(null)
  const [editDraft, setEditDraft] = useState<Partial<User>>({})

  async function createUser() {
    setSaving(true); setErr(null)
    try {
      const res = await fetch(`${API}/users`, {
        method:"POST", headers:{"content-type":"application/json"},
        body: JSON.stringify(form)
      })
      if (!res.ok) throw new Error(`Create failed: ${res.status}`)
      setForm({name:"", email:"", role:"nchd"})
      await refresh()
    } catch (e:any) {
      setErr(e.message || "Create failed")
    } finally {
      setSaving(false)
    }
  }

  async function saveEdit(id:number) {
    setSaving(true); setErr(null)
    try {
      const payload: any = {}
      if (editDraft.name !== undefined) payload.name = editDraft.name
      if (editDraft.email !== undefined) payload.email = editDraft.email
      if (editDraft.role !== undefined) payload.role = editDraft.role
      const res = await fetch(`${API}/users/${id}`, {
        method:"PATCH", headers:{"content-type":"application/json"},
        body: JSON.stringify(payload)
      })
      if (!res.ok) throw new Error(`Update failed: ${res.status}`)
      setEditing(null); setEditDraft({})
      await refresh()
    } catch (e:any) {
      setErr(e.message || "Update failed")
    } finally {
      setSaving(false)
    }
  }

  async function remove(id:number) {
    setSaving(true); setErr(null)
    try {
      const res = await fetch(`${API}/users/${id}`, { method:"DELETE" })
      if (!res.ok) throw new Error(`Delete failed: ${res.status}`)
      await refresh()
    } catch (e:any) {
      setErr(e.message || "Delete failed")
    } finally {
      setSaving(false)
    }
  }

  return (
    <div style={{marginTop:"1rem"}}>
      <h3 style={{marginBottom:8}}>Users (Admin)</h3>
      {err && <div style={{color:"crimson", marginBottom:8}}>Error: {err}</div>}

      {/* Create */}
      <div style={{display:"flex", gap:8, flexWrap:"wrap", alignItems:"center", marginBottom:12}}>
        <input placeholder="Name" value={form.name} onChange={e=>setForm({...form, name:e.target.value})}/>
        <input placeholder="Email" value={form.email} onChange={e=>setForm({...form, email:e.target.value})}/>
        <select value={form.role} onChange={e=>setForm({...form, role:e.target.value as Role})}>
          <option value="admin">admin</option>
          <option value="supervisor">supervisor</option>
          <option value="nchd">nchd</option>
          <option value="staff">staff</option>
        </select>
        <button onClick={createUser} disabled={saving || !form.name || !form.email}>Add user</button>
      </div>

      {/* List with inline edit/delete */}
      <div style={{overflowX:"auto"}}>
        <table style={{borderCollapse:"collapse", minWidth:700}}>
          <thead>
            <tr>
              <th style={th}>ID</th>
              <th style={th}>Name</th>
              <th style={th}>Email</th>
              <th style={th}>Role</th>
              <th style={th}>Actions</th>
            </tr>
          </thead>
          <tbody>
          {users.map(u=>(
            <tr key={u.id}>
              <td style={td}>{u.id}</td>
              <td style={td}>
                {editing===u.id ? (
                  <input defaultValue={u.name} onChange={e=>setEditDraft(d=>({...d, name:e.target.value}))}/>
                ) : u.name}
              </td>
              <td style={td}>
                {editing===u.id ? (
                  <input defaultValue={u.email} onChange={e=>setEditDraft(d=>({...d, email:e.target.value}))}/>
                ) : u.email}
              </td>
              <td style={td}>
                {editing===u.id ? (
                  <select defaultValue={u.role} onChange={e=>setEditDraft(d=>({...d, role:e.target.value as Role}))}>
                    <option value="admin">admin</option>
                    <option value="supervisor">supervisor</option>
                    <option value="nchd">nchd</option>
                    <option value="staff">staff</option>
                  </select>
                ) : <RoleBadge role={u.role}/>}
              </td>
              <td style={td}>
                {editing===u.id ? (
                  <>
                    <button onClick={()=>saveEdit(u.id)} disabled={saving}>Save</button>
                    <button onClick={()=>{setEditing(null); setEditDraft({})}} disabled={saving} style={{marginLeft:6}}>Cancel</button>
                  </>
                ) : (
                  <>
                    <button onClick={()=>{setEditing(u.id); setEditDraft({})}}>Edit</button>
                    <button onClick={()=>remove(u.id)} style={{marginLeft:6}}>Delete</button>
                  </>
                )}
              </td>
            </tr>
          ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export function App() {
  const { users, loading, error, refresh } = useUsers()
  const [tab, setTab] = useState<"Admin"|"Supervisor"|"NCHD"|"Staff">("Admin")

  // Filtered views (just to visually prove tabs switch)
  const nchds = useMemo(()=>users.filter(u=>u.role==="nchd"), [users])
  const supervisors = useMemo(()=>users.filter(u=>u.role==="supervisor"), [users])
  const admins = useMemo(()=>users.filter(u=>u.role==="admin"), [users])
  const staff = useMemo(()=>users.filter(u=>u.role==="staff"), [users])

  return (
    <div style={{fontFamily:"system-ui,-apple-system,Segoe UI,Roboto", margin:"2rem", lineHeight:1.35}}>
      <h1 style={{marginBottom:4}}>NCHD Rostering & Leave System</h1>
      <p style={{marginTop:0, color:"#555"}}>Demo UI — growing features.</p>

      {/* Tabs */}
      <div style={{margin:"1rem 0"}}>
        {(["Admin","Supervisor","NCHD","Staff"] as const).map(t =>
          <TabButton key={t} active={t===tab} onClick={()=>setTab(t)}>{t}</TabButton>
        )}
      </div>

      {/* Body — switches with tab */}
      {loading && <div>Loading…</div>}
      {error && <div style={{color:"crimson"}}>Error: {error}</div>}
      {!loading && !error && (
        <>
          {tab==="Admin" && (
            <>
              <p><strong>Admins:</strong> {admins.length}</p>
              <AdminUsers users={users} refresh={refresh}/>
            </>
          )}
          {tab==="Supervisor" && (
            <>
              <p><strong>Supervisors:</strong> {supervisors.length}</p>
              <UsersTable users={supervisors}/>
              <div style={{marginTop:12}}>Supervisor dashboard: team calendar, leave approvals (coming next).</div>
            </>
          )}
          {tab==="NCHD" && (
            <>
              <p><strong>NCHDs:</strong> {nchds.length}</p>
              <UsersTable users={nchds}/>
              <div style={{marginTop:12}}>NCHD dashboard: personal calendar, Leave Helper (coming next).</div>
            </>
          )}
          {tab==="Staff" && (
            <>
              <p><strong>Staff:</strong> {staff.length}</p>
              <UsersTable users={staff}/>
              <div style={{marginTop:12}}>Staff dashboard: operational week view (coming next).</div>
            </>
          )}
        </>
      )}
    </div>
  )
}

const th: React.CSSProperties = { textAlign:"left", borderBottom:"1px solid #ddd", padding:"8px 10px", fontWeight:600 }
const td: React.CSSProperties = { borderBottom:"1px solid #f0f0f0", padding:"8px 10px" }
