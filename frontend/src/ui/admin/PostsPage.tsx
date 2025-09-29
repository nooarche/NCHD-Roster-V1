import React, { useEffect, useState } from "react"
const API = (import.meta as any).env?.VITE_API_BASE || "/api"

type Post = { id:number; title:string; opd_day?:string|null }

export default function PostsPage() {
  const [rows, setRows] = useState<Post[]>([])
  const [form, setForm] = useState<{title:string; opd_day:string}>({title:"", opd_day:""})
  const [busy, setBusy] = useState(false)

  async function load(){ const r=await fetch(`${API}/posts`); setRows(await r.json()) }
  useEffect(()=>{ load() }, [])

  async function add(){
    setBusy(true)
    await fetch(`${API}/posts`, {method:"POST", headers:{"content-type":"application/json"}, body:JSON.stringify(form)})
    setForm({title:"", opd_day:""}); setBusy(false); load()
  }
  async function save(p:Post){
    await fetch(`${API}/posts/${p.id}`, {method:"PATCH", headers:{"content-type":"application/json"}, body:JSON.stringify({title:p.title, opd_day:p.opd_day||""})})
    load()
  }
  async function del(id:number){ await fetch(`${API}/posts/${id}`, {method:"DELETE"}); load() }

  return (
    <div>
      <h3>Posts</h3>
      <div style={{display:"flex", gap:8, marginBottom:10}}>
        <input placeholder="Title" value={form.title} onChange={e=>setForm({...form, title:e.target.value})}/>
        <input placeholder="OPD day (e.g. Wed)" value={form.opd_day} onChange={e=>setForm({...form, opd_day:e.target.value})}/>
        <button onClick={add} disabled={busy || !form.title}>Add</button>
      </div>
      <table style={{borderCollapse:"collapse", minWidth:520}}>
        <thead><tr><th>Id</th><th>Title</th><th>OPD day</th><th>Actions</th></tr></thead>
        <tbody>
          {rows.map(r=>(
            <tr key={r.id}>
              <td>{r.id}</td>
              <td><input value={r.title} onChange={e=>setRows(rows.map(x=>x.id===r.id?{...x,title:e.target.value}:x))}/></td>
              <td><input value={r.opd_day||""} onChange={e=>setRows(rows.map(x=>x.id===r.id?{...x,opd_day:e.target.value}:x))}/></td>
              <td><button onClick={()=>save(r)}>Save</button> <button onClick={()=>del(r.id)}>Delete</button></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
