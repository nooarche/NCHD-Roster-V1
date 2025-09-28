import React, { useEffect, useMemo, useState } from "react"

type Role = "admin" | "supervisor" | "nchd" | "staff"
type User = { id:number; name:string; email:string; role:Role }

// When running behind nginx we set VITE_API_BASE=/api in compose.
// Fallbacks so it still works direct on :8000 during dev.
const API = (import.meta as any).env?.VITE_API_BASE || "/api"

const th: React.CSSProperties = { textAlign:"left", borderBottom:"1px solid #ddd", padding:"8px 10px", fontWeight:600 }
const td: React.CSSProperties = { borderBottom:"1px solid #f0f0f0", padding:"8px 10px" }

function useUsers() {
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const refresh = async () => {
    setLoading(true); setError(null)
    try {
      const r = await fetch(`${API}/users`)
      if (!r.ok) throw new Error(`HTTP ${r.status}`)
      setUsers(await r.json())
    } catch (e:any) { setError(e.message || "Failed to load users") }
    finally { setLoading(false) }
  }
  useEffect(() => { refresh() }, [])
  return { users, loading, error, refresh }
}

const TabBtn: React.FC<{active:boolean; onClick:()=>void; label:string}> = ({active,onClick,label}) => (
  <button onClick={onClick}
    style={{padding:"0.5rem 1rem", marginRight:8, border:"1px solid #ddd",
            borderBottom: active ? "2px solid black" : "1px solid #ddd",
            background: active ? "#f8f8f8" : "white", cursor:"pointer", borderRadius:6}}>
    {label}
  </button>
)

const RoleBadge: React.FC<{role:Role}> = ({role}) => (
  <span style={{
    padding:"2px 8px", borderRadius:999, border:"1px solid #ddd", fontSize:12,
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
          <tr><th style={th}>ID</th><th style={th}>Name</th><th style={th}>Email</th><th style={th}>Role</th></tr>
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
  )
}

/** Admin panel: minimal create/edit/delete */
function AdminUsers({users, refresh}:{users:User[], refresh:()=>void}) {
  const [form, setForm] = useState<{name:string; email:string; role:Role}>({name:"", email:"", role:"nchd"})
  const [editing, setEditing] = useState<number|null>(null)
  const [draft, setDraft] = useState<Partial<User>>({})
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState<string|null>(null)

  async function create() {
    setBusy(true); setErr(null)
    try {
      const r = await fetch(`${API}/users`, { method:"POST", headers:{ "content-type":"application/json" }, body:JSON.stringify(form) })
      if (!r.ok) throw new Error(`Create failed: ${r.status}`)
      setForm({name:"", email:"", role:"nchd"}); await refresh()
    } catch(e:any){ setErr(e.message) } finally { setBusy(false) }
  }
  async function save(id:number) {
    setBusy(true); setErr(null)
    try {
      const payload:any = {}; if(draft.name!==undefined) payload.name=draft.name; if(draft.email!==undefined) payload.email=draft.email; if(draft.role!==undefined) payload.role=draft.role
      const r = await fetch(`${API}/users/${id}`, { method:"PATCH", headers:{ "content-type":"application/json" }, body:JSON.stringify(payload) })
      if (!r.ok) throw new Error(`Update failed: ${r.status}`)
      setEditing(null); setDraft({}); await refresh()
    } catch(e:any){ setErr(e.message) } finally { setBusy(false) }
  }
  async function remove(id:number){
    setBusy(true); setErr(null)
    try{
      const r = await fetch(`${API}/users/${id}`, { method:"DELETE" })
      if(!r.ok) throw new Error(`Delete failed: ${r.status}`)
      await refresh()
    } catch(e:any){ setErr(e.message) } finally { setBusy(false) }
  }

  return (
    <div style={{marginTop:12}}>
      {err && <div style={{color:"crimson", marginBottom:8}}>Error: {err}</div>}
      {/* Create */}
      <div style={{display:"flex", gap:8, flexWrap:"wrap", alignItems:"center", marginBottom:12}}>
        <input placeholder="Name" value={form.name} onChange={e=>setForm({...form, name:e.target.value})}/>
        <input placeholder="Email" value={form.email} onChange={e=>setForm({...form, email:e.target.value})}/>
        <select value={form.role} onChange={e=>setForm({...form, role:e.target.value as Role})}>
          <option value="admin">admin</option><option value="supervisor">supervisor</option>
          <option value="nchd">nchd</option><option value="staff">staff</option>
        </select>
        <button onClick={create} disabled={busy || !form.name || !form.email}>Add user</button>
      </div>

      {/* List with inline edit/delete */}
      <div style={{overflowX:"auto"}}>
        <table style={{borderCollapse:"collapse", minWidth:700}}>
          <thead>
            <tr><th style={th}>ID</th><th style={th}>Name</th><th style={th}>Email</th><th style={th}>Role</th><th style={th}>Actions</th></tr>
          </thead>
          <tbody>
            {users.map(u=>(
              <tr key={u.id}>
                <td style={td}>{u.id}</td>
                <td style={td}>{editing===u.id ? <input defaultValue={u.name} onChange={e=>setDraft(d=>({...d, name:e.target.value}))}/> : u.name}</td>
                <td style={td}>{editing===u.id ? <input defaultValue={u.email} onChange={e=>setDraft(d=>({...d, email:e.target.value}))}/> : u.email}</td>
                <td style={td}>
                  {editing===u.id ? (
                    <select defaultValue={u.role} onChange={e=>setDraft(d=>({...d, role:e.target.value as Role}))}>
                      <option value="admin">admin</option><option value="supervisor">supervisor</option>
                      <option value="nchd">nchd</option><option value="staff">staff</option>
                    </select>
                  ) : <RoleBadge role={u.role}/>}
                </td>
                <td style={td}>
                  {editing===u.id
                    ? (<><button onClick={()=>save(u.id)} disabled={busy}>Save</button>
                         <button onClick={()=>{setEditing(null); setDraft({})}} style={{marginLeft:6}} disabled={busy}>Cancel</button></>)
                    : (<><button onClick={()=>{setEditing(u.id); setDraft({})}}>Edit</button>
                         <button onClick={()=>remove(u.id)} style={{marginLeft:6}}>Delete</button></>)
                  }
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

  const admins = useMemo(()=>users.filter(u=>u.role==="admin"), [users])
  const supervisors = useMemo(()=>users.filter(u=>u.role==="supervisor"), [users])
  const nchds = useMemo(()=>users.filter(u=>u.role==="nchd"), [users])
  const staff = useMemo(()=>users.filter(u=>u.role==="staff"), [users])

  return (
    <div style={{fontFamily:"system-ui,-apple-system,Segoe UI,Roboto", margin:"2rem", lineHeight:1.35}}>
      <h1 style={{marginBottom:4}}>NCHD Rostering & Leave System</h1>
      <p style={{marginTop:0, color:"#555"}}>Demo UI — growing features.</p>

      <div style={{margin:"1rem 0"}}>
        {(["Admin","Supervisor","NCHD","Staff"] as const).map(t =>
          <TabBtn key={t} active={t===tab} onClick={()=>setTab(t)} label={t} />
        )}
      </div>

      {loading && <div>Loading…</div>}
      {error && <div style={{color:"crimson"}}>Error: {error}</div>}

      {!loading && !error && (
        <>
          {tab==="Admin" && (
            <>
              <h2 style={{margin:"8px 0"}}>Admin view</h2>
              <p><strong>Admins:</strong> {admins.length}</p>
              <AdminUsers users={users} refresh={refresh}/>
            </>
          )}
          {tab==="Supervisor" && (
            <>
              <h2 style={{margin:"8px 0"}}>Supervisor view</h2>
              <p><strong>Supervisors:</strong> {supervisors.length}</p>
              <UsersTable users={supervisors}/>
              <div style={{marginTop:12}}>Team calendar & approvals (coming soon).</div>
            </>
          )}
          {tab==="NCHD" && (
            <>
              <h2 style={{margin:"8px 0"}}>NCHD view</h2>
              <p><strong>NCHDs:</strong> {nchds.length}</p>
              <UsersTable users={nchds}/>
              <div style={{marginTop:12}}>Personal calendar & Leave Helper (coming soon).</div>
            </>
          )}
          {tab==="Staff" && (
            <>
              <h2 style={{margin:"8px 0"}}>Staff view</h2>
              <p><strong>Staff:</strong> {staff.length}</p>
              <UsersTable users={staff}/>
              <div style={{marginTop:12}}>Operational week view (coming soon).</div>
            </>
          )}
        </>
      )}
    </div>
  )
}
