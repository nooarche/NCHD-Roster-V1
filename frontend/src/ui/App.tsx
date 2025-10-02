import React, { useEffect, useMemo, useState } from "react"
import { AdminNav, AdminTab } from "./admin/AdminNav"
import PostsPage from "./admin/PostsPage"
import TeamsPage from "./admin/TeamsPage"
import ContractsPage from "./admin/ContractsPage"
import AdminOncallPage from "./admin/AdminOncallPage"



type Role = "admin" | "supervisor" | "nchd" | "staff"
type User = { id:number; name:string; email:string; role:Role }
type OnCallEvent = { start:string; end:string; type:string; user_id:number; user_name:string }
type ValidationIssue = { user_id:number; user_name:string; slot_id:number; message:string }
type ValidationReport = { ok:boolean; issues:ValidationIssue[] }

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

/** ===== Admin: On-call rules + validation + Users CRUD ===== */
function AdminPanel({users, refresh}:{users:User[], refresh:()=>void}) {
  const [subtab, setSubtab] = useState<AdminTab>("Users")
  return (
    <div>
      <h2 style={{margin:"8px 0"}}>Admin</h2>
      <AdminNav active={subtab} onChange={setSubtab}/>
      {subtab==="Users" && <AdminUsers users={users} refresh={refresh}/>}
      {subtab==="Posts" && <PostsPage/>}
      {subtab==="Teams" && <TeamsPage/>}
      {subtab==="Contracts" && <ContractsPage/>}
      {subtab==="On-call" && (<>
        <ValidationCard/>
        {/* You can reuse Staff calendar here and add edit modal later */}
      </>)}
      {subtab==="On-call" && <AdminOncallPage/>}
      {subtab==="Core Hours" && <div>Core hours profiles/overrides (next)</div>}
      {subtab==="OPD" && <div>OPD sessions editor (next)</div>}
      {subtab==="Supervision" && <div>Supervision slots editor (next)</div>}
    </div>
  )
}

function OnCallRules() {
  return (
    <div style={{margin:"12px 0", padding:"12px", border:"1px solid #eee", borderRadius:8}}>
      <h3 style={{marginTop:0}}>On-call rota rules (summary)</h3>
      <ul>
        <li>Exactly one on-call (day or night) covering each required period.</li>
        <li>Duty length ≤ 24 hours (EWTD hard cap).</li>
        <li>Daily rest ≥ 11 hours; weekly rest ≥ 24 hours (rolling windows).</li>
        <li>Protected teaching (e.g., Wed 14:00–16:30) not to be overridden by call.</li>
        <li>Handover blocks observed at boundaries (e.g., 16:30–17:00, 09:00–09:30).</li>
        <li>Fair distribution of on-call across NCHDs over the rotation.</li>
      </ul>
      <small>Full contract/EWTD mapping to be expanded in compliance module.</small>
    </div>
  )
}

function ValidationCard() {
  const [report, setReport] = useState<ValidationReport | null>(null)
  const [busy, setBusy] = useState(false)
  const run = async () => {
    setBusy(true)
    try {
      const r = await fetch(`${API}/validate/rota`)
      const data = await r.json()
      setReport(data)
    } finally { setBusy(false) }
  }
  return (
    <div style={{margin:"12px 0", padding:"12px", border:"1px solid #eee", borderRadius:8}}>
      <div style={{display:"flex", alignItems:"center", gap:12}}>
        <h3 style={{margin:0}}>Rota validation</h3>
        <button onClick={run} disabled={busy}>{busy ? "Running…" : "Run validation"}</button>
        {report && <span style={{fontWeight:600, color: report.ok ? "green" : "crimson"}}>
          {report.ok ? "OK — no issues found" : `${report.issues.length} issue(s)`}
        </span>}
      </div>
      {report && !report.ok && (
        <ol style={{marginTop:12}}>
          {report.issues.map((i, idx) => (
            <li key={idx}><code>slot#{i.slot_id}</code> — {i.user_name}: {i.message}</li>
          ))}
        </ol>
      )}
    </div>
  )
}




function usePosts() {
  const [posts, setPosts] = useState<any[]>([])
  const refresh = () => fetch(`${API}/posts`).then(r=>r.json()).then(setPosts).catch(()=>{})
  useEffect(refresh, [])
  return { posts, refresh }
}

export function App() {
  const users = useUsers()
  const { posts, refresh } = usePosts()
  const [form, setForm] = useState<any>({ title:"", site:"", grade:"", fte:1.0, status:"ACTIVE_ROSTERABLE" })
  const save = async () => {
    await fetch(`${API}/posts`, { method:"POST", headers:{ "Content-Type":"application/json" }, body:JSON.stringify(form) })
    setForm({ title:"", site:"", grade:"", fte:1.0, status:"ACTIVE_ROSTERABLE" })
    refresh()
  }
  const addVacancy = async (postId:number) => {
    const payload = { status:"VACANT_UNROSTERABLE", start_date:new Date().toISOString().slice(0,10) }
    await fetch(`${API}/posts/${postId}/vacancy`, { method:"POST", headers:{ "Content-Type":"application/json" }, body:JSON.stringify(payload) })
    refresh()
  }

  return (
    <div style={{fontFamily:"system-ui", margin:"2rem", display:"grid", gap:"1.5rem"}}>
      <h1>NCHD Rostering & Leave System</h1>

      <section>
        <h2>Admin · Post Builder</h2>
        <div style={{display:"grid", gap:"0.5rem", maxWidth:520}}>
          <input placeholder="Title" value={form.title} onChange={e=>setForm({...form, title:e.target.value})}/>
          <input placeholder="Site" value={form.site} onChange={e=>setForm({...form, site:e.target.value})}/>
          <input placeholder="Grade" value={form.grade} onChange={e=>setForm({...form, grade:e.target.value})}/>
          <input placeholder="FTE (0.1–1.0)" type="number" step="0.1" value={form.fte} onChange={e=>setForm({...form, fte:parseFloat(e.target.value)})}/>
          <select value={form.status} onChange={e=>setForm({...form, status:e.target.value})}>
            <option>ACTIVE_ROSTERABLE</option>
            <option>VACANT_ROSTERABLE</option>
            <option>VACANT_UNROSTERABLE</option>
          </select>
          <button onClick={save}>Save Post</button>
        </div>
      </section>

      <section>
        <h2>Posts</h2>
        <ul>
          {posts.map(p => (
            <li key={p.id} style={{marginBottom:"0.75rem"}}>
              <strong>{p.title}</strong> · {p.site} · {p.grade} · FTE {p.fte} · <em>{p.status}</em>{" "}
              <button onClick={()=>addVacancy(p.id)}>Mark Unrosterable (from today)</button>
            </li>
          ))}
        </ul>
      </section>

      <section>
        <h2>Users</h2>
        <ul>
          {users.map(u => <li key={u.id}>{u.name} — {u.role}</li>)}
        </ul>
      </section>
    </div>
  )
}

function useUsers() {
  const [users, setUsers] = useState<any[]>([])
  useEffect(() => {
    fetch(`${API}/users`).then(r => r.json()).then(setUsers).catch(()=>{})
  }, [])
  return users
}

/** Admin: Users CRUD */
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
      <h3>Users (Admin)</h3>
      {err && <div style={{color:"crimson", marginBottom:8}}>Error: {err}</div>}
      <div style={{display:"flex", gap:8, flexWrap:"wrap", alignItems:"center", marginBottom:12}}>
        <input placeholder="Name" value={form.name} onChange={e=>setForm({...form, name:e.target.value})}/>
        <input placeholder="Email" value={form.email} onChange={e=>setForm({...form, email:e.target.value})}/>
        <select value={form.role} onChange={e=>setForm({...form, role:e.target.value as Role})}>
          <option value="admin">admin</option><option value="supervisor">supervisor</option>
          <option value="nchd">nchd</option><option value="staff">staff</option>
        </select>
        <button onClick={create} disabled={busy || !form.name || !form.email}>Add user</button>
      </div>
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

/** ===== Staff: Monthly on-call calendar ===== */
function StaffCalendar() {
  const today = new Date()
  const [year, setYear] = useState<number>(today.getFullYear())
  const [month, setMonth] = useState<number>(today.getMonth()+1) // 1..12
  const [events, setEvents] = useState<OnCallEvent[]>([])

  async function load() {
    const r = await fetch(`${API}/oncall/month?year=${year}&month=${month}`)
    setEvents(await r.json())
  }
  useEffect(()=>{ load() }, [year, month])

  const first = new Date(year, month-1, 1)
  const startDay = first.getDay()  // 0 Sun .. 6 Sat
  const daysInMonth = new Date(year, month, 0).getDate()
  const cells: {day?:number; notes?:string[]}[] = []
  for (let i=0;i<startDay;i++) cells.push({})
  for (let d=1; d<=daysInMonth; d++) cells.push({day:d})

  // Map events per day label
  const perDay = new Map<number, string[]>()
  for (const ev of events) {
    const s = new Date(ev.start)
    const d = s.getDate()
    const label = `${ev.type==="night_call"?"Night":"Day"}: ${ev.user_name}`
    perDay.set(d, [...(perDay.get(d)||[]), label])
  }

  return (
    <div style={{marginTop:8}}>
      <div style={{display:"flex", alignItems:"center", gap:8, marginBottom:8}}>
        <button onClick={()=>{ const nm = new Date(year, month-2, 1); setYear(nm.getFullYear()); setMonth(nm.getMonth()+1) }}>◀</button>
        <strong>{first.toLocaleString(undefined,{month:"long"})} {year}</strong>
        <button onClick={()=>{ const nm = new Date(year, month, 1); setYear(nm.getFullYear()); setMonth(nm.getMonth()+1) }}>▶</button>
        <button onClick={load}>Reload</button>
      </div>
      <div style={{display:"grid", gridTemplateColumns:"repeat(7, 1fr)", gap:6}}>
        {["Sun","Mon","Tue","Wed","Thu","Fri","Sat"].map(w=>(
          <div key={w} style={{textAlign:"center", fontWeight:600}}>{w}</div>
        ))}
        {cells.map((c, idx)=>(
          <div key={idx} style={{minHeight:90, border:"1px solid #eee", borderRadius:6, padding:6}}>
            {c.day && <div style={{fontWeight:600, marginBottom:6}}>{c.day}</div>}
            {c.day && (perDay.get(c.day)||[]).map((t,i)=>(
              <div key={i} style={{fontSize:12, marginBottom:4}}>{t}</div>
            ))}
          </div>
        ))}
      </div>
    </div>
  )
}

function RosterBuilder() {
  const now = new Date()
  const [year, setYear] = useState(now.getFullYear())
  const [month, setMonth] = useState(now.getMonth()+1)
  const [busy, setBusy] = useState(false)
  const [msg, setMsg] = useState<string | null>(null)

  async function build() {
    setBusy(true); setMsg(null)
    try {
      const r = await fetch(`${API}/actions/roster-build`, {
        method:"POST",
        headers:{ "content-type":"application/json" },
        body: JSON.stringify({
          year, month,
          day_calls_per_day: 0,
          night_calls_per_day: 1,
          pool_roles: ["nchd"]   // round-robin across NCHDs
        })
      })
      const data = await r.json()
      if (!r.ok) throw new Error(data.detail || `HTTP ${r.status}`)
      setMsg(`Created ${data.created_slots} on-call slots for ${year}-${String(month).padStart(2,"0")}.`)
    } catch(e:any) {
      setMsg(e.message || "Build failed")
    } finally { setBusy(false) }
  }

  return (
    <div style={{margin:"12px 0", padding:"12px", border:"1px solid #eee", borderRadius:8}}>
      <h3 style={{marginTop:0}}>Roster builder</h3>
      <div style={{display:"flex", gap:8, alignItems:"center", flexWrap:"wrap"}}>
        <input type="number" value={year} onChange={e=>setYear(parseInt(e.target.value||`${now.getFullYear()}`,10))} style={{width:100}}/>
        <input type="number" value={month} min={1} max={12} onChange={e=>setMonth(parseInt(e.target.value||"1",10))} style={{width:80}}/>
        <button onClick={build} disabled={busy}>{busy ? "Building…" : "Build roster"}</button>
        {msg && <span>{msg}</span>}
      </div>
      <small>Round-robin across NCHDs. Re-running will overwrite existing on-call slots for that month.</small>
    </div>
  )
}

export function App() {
  const { users, loading, error, refresh } = useUsers()
  const [tab, setTab] = useState<"Admin"|"Supervisor"|"NCHD"|"Staff">("Admin")

  const supervisors = useMemo(()=>users.filter(u=>u.role==="supervisor"), [users])
  const nchds = useMemo(()=>users.filter(u=>u.role==="nchd"), [users])

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
          {tab==="Admin"      && <AdminPanel users={users} refresh={refresh}/>}
          {tab==="Supervisor" && (<>
            <h2>Supervisor view</h2>
            <UsersTable users={supervisors}/>
            <div style={{marginTop:12}}>Team calendar & approvals (coming soon).</div>
          </>)}
          {tab==="NCHD"       && (<>
            <h2>NCHD view</h2>
            <UsersTable users={nchds}/>
            <div style={{marginTop:12}}>Personal calendar & Leave Helper (coming soon).</div>
          </>)}
          {tab==="Staff"      && (<>
            <h2>Staff view — Monthly on-call</h2>
            <StaffCalendar/>
          </>)}
        </>
      )}
    </div>
  )
}
