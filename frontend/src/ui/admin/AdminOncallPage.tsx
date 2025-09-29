import React, { useEffect, useMemo, useState } from "react"
import ValidationCard from "./ValidationCard"

const API = (import.meta as any).env?.VITE_API_BASE || "/api"

type User = { id:number; name:string; role:string }
type Event = { slot_id:number; start:string; end:string; type:string; user_id:number; user_name:string }
type Post = { id:number; title:string }

function ymd(d: Date){ return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,"0")}-${String(d.getDate()).padStart(2,"0")}` }

export default function AdminOncallPage(){
  const now = new Date()
  const [year, setYear] = useState(now.getFullYear())
  const [month, setMonth] = useState(now.getMonth()+1) // 1..12
  const [events, setEvents] = useState<Event[]>([])
  const [users, setUsers] = useState<User[]>([])
  const [posts, setPosts] = useState<Post[]>([])
  const [open, setOpen] = useState(false)
  const [selectedDate, setSelectedDate] = useState<Date | null>(null)
  const [selectedSlot, setSelectedSlot] = useState<Event | null>(null)
  const [assignUserId, setAssignUserId] = useState<string>("")
  const [assignPostId, setAssignPostId] = useState<string>("")

  async function load(){
    const [ev, us, ps] = await Promise.all([
      fetch(`${API}/oncall/month?year=${year}&month=${month}`).then(r=>r.json()),
      fetch(`${API}/users`).then(r=>r.json()),
      fetch(`${API}/posts`).then(r=>r.json()),
    ])
    setEvents(ev)
    setUsers(us.filter((u:User)=>u.role==="nchd"))
    setPosts(ps)
  }
  useEffect(()=>{ load() }, [year, month])

  function openModalForDate(d: Date){
    setSelectedDate(d)
    // see if there's already a night_call that starts that day 17:00
    const key = ymd(d)
    const existing = events.find(e => e.type==="night_call" && e.start.startsWith(key))
    setSelectedSlot(existing || null)
    setAssignUserId(existing ? String(existing.user_id) : "")
    setAssignPostId("")
    setOpen(true)
  }

  async function assign(){
    if (!selectedDate || !assignUserId) return
    const start = new Date(selectedDate); start.setHours(17,0,0,0)
    const end = new Date(selectedDate); end.setDate(end.getDate()+1); end.setHours(9,0,0,0)
    await fetch(`${API}/oncall/assign`, {
      method:"POST",
      headers:{"content-type":"application/json"},
      body: JSON.stringify({
        user_id: Number(assignUserId),
        post_id: assignPostId ? Number(assignPostId) : undefined,
        start: start.toISOString(),
        end: end.toISOString(),
        type: "night_call"
      })
    })
    setOpen(false); await load()
  }

  async function remove(){
    if (!selectedSlot) return
    await fetch(`${API}/oncall/${selectedSlot.slot_id}`, { method: "DELETE" })
    setOpen(false); await load()
  }

  async function buildMonth(){
    await fetch(`${API}/actions/roster-build`, {
      method:"POST",
      headers:{"content-type":"application/json"},
      body: JSON.stringify({ year, month, day_calls_per_day:0, night_calls_per_day:1, pool_roles:["nchd"] })
    })
    await load()
  }

  // Autofill by Post for this month
  const [autoPostId, setAutoPostId] = useState<string>("")
  async function autofillByPost(){
    if (!autoPostId) return
    await fetch(`${API}/actions/autofill-by-post`, {
      method:"POST",
      headers:{"content-type":"application/json"},
      body: JSON.stringify({ post_id: Number(autoPostId), year, month })
    })
    await load()
  }

  // Simple calendar grid (focus on click/edit)
  const first = useMemo(()=> new Date(year, month-1, 1), [year, month])
  const daysInMonth = useMemo(()=> new Date(year, month, 0).getDate(), [year, month])
  const monthName = first.toLocaleString(undefined, { month:"long" })

  return (
    <div>
      <div style={{display:"flex", alignItems:"center", gap:8, marginBottom:12}}>
        <button onClick={()=>{ const d=new Date(year,month-2,1); setYear(d.getFullYear()); setMonth(d.getMonth()+1) }}>◀</button>
        <strong>{monthName} {year}</strong>
        <button onClick={()=>{ const d=new Date(year,month,1); setYear(d.getFullYear()); setMonth(d.getMonth()+1) }}>▶</button>
        <button onClick={load}>Reload</button>
        <button onClick={buildMonth}>Build (contracts-aware)</button>
        <span style={{marginLeft:"auto",fontSize:12,color:"#666"}}>{events.length} events</span>
      </div>

      <ValidationCard year={year} month={month} /> 
      
      {/* Autofill panel */}
      <div style={{display:"flex", alignItems:"center", gap:8, padding:8, border:"1px solid #eee", borderRadius:6, marginBottom:10}}>
        <span>Autofill nights by Post (this month):</span>
        <select value={autoPostId} onChange={e=>setAutoPostId(e.target.value)}>
          <option value="">Select post…</option>
          {posts.map(p => <option key={p.id} value={p.id}>{p.title}</option>)}
        </select>
        <button onClick={autofillByPost} disabled={!autoPostId}>Autofill</button>
      </div>

      {/* Calendar */}
      <div style={{display:"grid", gridTemplateColumns:"repeat(7, 1fr)", gap:6}}>
        {Array.from({length: daysInMonth}, (_,i)=>i+1).map(day=>{
          const d = new Date(year, month-1, day)
          const key = ymd(d)
          const ev = events.find(e => e.type==="night_call" && e.start.startsWith(key))
          return (
            <div key={day} onClick={()=>openModalForDate(d)}
                 style={{border:"1px solid #ddd", borderRadius:6, padding:8, cursor:"pointer", minHeight:72}}>
              <div style={{fontSize:12, color:"#666"}}>{day}</div>
              {ev ? (
                <div style={{marginTop:6}}>
                  <div style={{fontSize:13, fontWeight:600}}>Night: {ev.user_name}</div>
                  <div style={{fontSize:11}}>{new Date(ev.start).toLocaleTimeString([], {hour:"2-digit",minute:"2-digit"})}-{new Date(ev.end).toLocaleTimeString([], {hour:"2-digit",minute:"2-digit"})}</div>
                </div>
              ): <div style={{marginTop:6, fontSize:12, color:"#aaa"}}>— unassigned —</div>}
            </div>
          )
        })}
      </div>

      {/* Modal */}
      {open && (
        <div style={{position:"fixed", inset:0, background:"rgba(0,0,0,0.35)", display:"flex", alignItems:"center", justifyContent:"center"}}>
          <div style={{background:"white", padding:16, width:420, borderRadius:8, boxShadow:"0 10px 30px rgba(0,0,0,0.2)"}}>
            <h4 style={{marginTop:0}}>Edit night call — {selectedDate ? selectedDate.toDateString() : ""}</h4>
            <div style={{display:"grid", gridTemplateColumns:"1fr 1fr", gap:8, marginBottom:12}}>
              <div>
                <label style={{display:"block", fontSize:12, color:"#666"}}>NCHD</label>
                <select style={{width:"100%"}} value={assignUserId} onChange={e=>setAssignUserId(e.target.value)}>
                  <option value="">Select NCHD…</option>
                  {users.map(u => <option key={u.id} value={u.id}>{u.name}</option>)}
                </select>
              </div>
              <div>
                <label style={{display:"block", fontSize:12, color:"#666"}}>Post (optional)</label>
                <select style={{width:"100%"}} value={assignPostId} onChange={e=>setAssignPostId(e.target.value)}>
                  <option value="">(use contract’s post)</option>
                  {posts.map(p => <option key={p.id} value={p.id}>{p.title}</option>)}
                </select>
              </div>
            </div>

            <div style={{display:"flex", gap:8, justifyContent:"flex-end"}}>
              {selectedSlot && <button onClick={remove} style={{color:"#b00"}}>Delete slot</button>}
              <button onClick={()=>setOpen(false)}>Cancel</button>
              <button onClick={assign} disabled={!assignUserId}>Save</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
