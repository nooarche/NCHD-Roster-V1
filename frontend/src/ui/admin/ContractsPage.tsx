import React, { useEffect, useState } from "react"
const API = (import.meta as any).env?.VITE_API_BASE || "/api"

type User = { id:number; name:string; role:string }
type Post = { id:number; title:string }
type Team = { id:number; name:string }
type Contract = { id:number; user_id:number; post_id:number; team_id?:number|null; start:string; end?:string|null }

export default function ContractsPage(){
  const [users, setUsers] = useState<User[]>([])
  const [posts, setPosts] = useState<Post[]>([])
  const [teams, setTeams] = useState<Team[]>([])
  const [rows, setRows] = useState<Contract[]>([])
  const [form, setForm] = useState<{user_id:string; post_id:string; team_id:string; start:string; end:string}>({user_id:"", post_id:"", team_id:"", start:"", end:""})

  async function load(){
    const [u,p,t,c] = await Promise.all([
      fetch(`${API}/users`).then(r=>r.json()),
      fetch(`${API}/posts`).then(r=>r.json()),
      fetch(`${API}/teams`).then(r=>r.json()),
      fetch(`${API}/contracts`).then(r=>r.json()),
    ])
    setUsers(u); setPosts(p); setTeams(t); setRows(c)
  }
  useEffect(()=>{ load() }, [])

  async function add(){
    const body: any = {
      user_id: Number(form.user_id),
      post_id: Number(form.post_id),
      start: form.start || new Date().toISOString().slice(0,10)
    }
    if (form.team_id) body.team_id = Number(form.team_id)
    if (form.end) body.end = form.end
    const r = await fetch(`${API}/contracts`, {method:"POST", headers:{"content-type":"application/json"}, body:JSON.stringify(body)})
    if (!r.ok) alert("Failed (overlap?)")
    setForm({user_id:"", post_id:"", team_id:"", start:"", end:""})
    load()
  }
  async function save(c:Contract){ await fetch(`${API}/contracts/${c.id}`, {method:"PATCH", headers:{"content-type":"application/json"}, body:JSON.stringify(c)}); load() }
  async function del(id:number){ await fetch(`${API}/contracts/${id}`, {method:"DELETE"}); load() }

  return (
    <div>
      <h3>Contracts</h3>
      <div style={{display:"flex", gap:8, flexWrap:"wrap", marginBottom:10}}>
        <select value={form.user_id} onChange={e=>setForm({...form, user_id:e.target.value})}>
          <option value="">User…</option>{users.map(u=><option key={u.id} value={u.id}>{u.name}</option>)}
        </select>
        <select value={form.post_id} onChange={e=>setForm({...form, post_id:e.target.value})}>
          <option value="">Post…</option>{posts.map(p=><option key={p.id} value={p.id}>{p.title}</option>)}
        </select>
        <select value={form.team_id} onChange={e=>setForm({...form, team_id:e.target.value})}>
          <option value="">(Team optional)</option>{teams.map(t=><option key={t.id} value={t.id}>{t.name}</option>)}
        </select>
        <input type="date" value={form.start} onChange={e=>setForm({...form, start:e.target.value})} placeholder="start"/>
        <input type="date" value={form.end} onChange={e=>setForm({...form, end:e.target.value})} placeholder="end (optional)"/>
        <button onClick={add} disabled={!form.user_id || !form.post_id}>Add</button>
      </div>

      <table style={{borderCollapse:"collapse", minWidth:800}}>
        <thead><tr><th>Id</th><th>User</th><th>Post</th><th>Team</th><th>Start</th><th>End</th><th>Actions</th></tr></thead>
        <tbody>
          {rows.map(r=>{
            const u = users.find(x=>x.id===r.user_id)?.name || r.user_id
            const p = posts.find(x=>x.id===r.post_id)?.title || r.post_id
            const t = r.team_id ? (teams.find(x=>x.id===r.team_id)?.name || r.team_id) : ""
            return (
              <tr key={r.id}>
                <td>{r.id}</td>
                <td>{u}</td>
                <td>{p}</td>
                <td>{t}</td>
                <td><input type="date" value={r.start.slice(0,10)} onChange={e=>setRows(rows.map(x=>x.id===r.id?{...x,start:e.target.value}:x))}/></td>
                <td><input type="date" value={(r.end||"").slice(0,10)} onChange={e=>setRows(rows.map(x=>x.id===r.id?{...x,end:e.target.value}:x))}/></td>
                <td><button onClick={()=>save(r)}>Save</button> <button onClick={()=>del(r.id)}>Delete</button></td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
