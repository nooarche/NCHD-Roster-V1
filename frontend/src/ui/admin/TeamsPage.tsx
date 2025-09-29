import React, { useEffect, useState } from "react"
const API = (import.meta as any).env?.VITE_API_BASE || "/api"

type User = { id:number; name:string; role:"admin"|"supervisor"|"nchd"|"staff" }
type Team = { id:number; name:string; supervisor_id?:number|null }

export default function TeamsPage(){
  const [teams, setTeams] = useState<Team[]>([])
  const [supers, setSupers] = useState<User[]>([])
  const [form, setForm] = useState<{name:string; supervisor_id:string}>({name:"", supervisor_id:""})
  async function load(){
    const [t,u] = await Promise.all([fetch(`${API}/teams`).then(r=>r.json()), fetch(`${API}/users`).then(r=>r.json())])
    setTeams(t); setSupers(u.filter((x:User)=>x.role==="supervisor"))
  }
  useEffect(()=>{ load() }, [])

  async function add(){
    await fetch(`${API}/teams`, {method:"POST", headers:{"content-type":"application/json"}, body:JSON.stringify({
      name: form.name, supervisor_id: form.supervisor_id ? Number(form.supervisor_id) : null
    })}); setForm({name:"", supervisor_id:""}); load()
  }
  async function save(t:Team){ await fetch(`${API}/teams/${t.id}`, {method:"PATCH", headers:{"content-type":"application/json"}, body:JSON.stringify(t)}); load() }
  async function del(id:number){ await fetch(`${API}/teams/${id}`, {method:"DELETE"}); load() }

  return (
    <div>
      <h3>Teams</h3>
      <div style={{display:"flex", gap:8, marginBottom:10}}>
        <input placeholder="Team name" value={form.name} onChange={e=>setForm({...form, name:e.target.value})}/>
        <select value={form.supervisor_id} onChange={e=>setForm({...form, supervisor_id:e.target.value})}>
          <option value="">(no supervisor)</option>
          {supers.map(s=> <option key={s.id} value={s.id}>{s.name}</option>)}
        </select>
        <button onClick={add} disabled={!form.name}>Add</button>
      </div>
      <table style={{borderCollapse:"collapse", minWidth:520}}>
        <thead><tr><th>Id</th><th>Name</th><th>Supervisor</th><th>Actions</th></tr></thead>
        <tbody>
          {teams.map(t=>(
            <tr key={t.id}>
              <td>{t.id}</td>
              <td><input value={t.name} onChange={e=>setTeams(teams.map(x=>x.id===t.id?{...x,name:e.target.value}:x))}/></td>
              <td>
                <select value={t.supervisor_id || ""} onChange={e=>setTeams(teams.map(x=>x.id===t.id?{...x,supervisor_id: e.target.value ? Number(e.target.value) : null}:x))}>
                  <option value="">(none)</option>
                  {supers.map(s=> <option key={s.id} value={s.id}>{s.name}</option>)}
                </select>
              </td>
              <td><button onClick={()=>save(t)}>Save</button> <button onClick={()=>del(t.id)}>Delete</button></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
