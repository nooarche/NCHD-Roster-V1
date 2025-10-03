// frontend/src/ui/AdminPostBuilder.tsx
import React, { useEffect, useState } from "react"

type Post = {
  id: number
  title: string
  site?: string
  grade?: string
  fte: number
  status: "ACTIVE_ROSTERABLE" | "VACANT_ROSTERABLE" | "VACANT_UNROSTERABLE"
}

type Props = { apiBase: string }

async function jsonFetch(url: string, init?: RequestInit) {
  const r = await fetch(url, {
    headers: { Accept: "application/json", ...(init?.headers || {}) },
    ...init,
  })
  const ct = r.headers.get("content-type") || ""
  if (!r.ok) {
    const text = await r.text()
    throw new Error(`${r.status} ${r.statusText} from ${url}\n${text.slice(0,200)}`)
  }
  if (!ct.includes("application/json")) {
    const text = await r.text()
    throw new Error(`Non-JSON from ${url} → starts with: ${text.slice(0,50)}`)
  }
  return r.json()
}

// replace your refresh() with:
const refresh = async () => {
  try {
    const [posts, users] = await Promise.all([
      jsonFetch(`${apiBase}/posts`),
      jsonFetch(`${apiBase}/users`)
    ])
    setPosts(posts)
    setError(null)
  } catch (e: any) {
    console.error(e)
    setError(e.message ?? String(e))
  }
}

export default function AdminPostBuilder({ apiBase }: Props) {
  const [posts, setPosts] = useState<Post[]>([])
  const [form, setForm] = useState<Partial<Post>>({
    title: "",
    site: "",
    grade: "",
    fte: 1.0,
    status: "ACTIVE_ROSTERABLE",
  })
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState<string | null>(null)

const refresh = async () => {
  try {
    const r = await fetch(`${apiBase}/posts`)
    if (!r.ok) {
      // capture textual error so the UI can show it instead of crashing
      const msg = await r.text()
      throw new Error(`GET /posts → ${r.status} ${r.statusText}: ${msg.slice(0,200)}`)
    }
    setPosts(await r.json())
    setError(null)
  } catch (e: any) {
    console.error(e)
    setError(e.message || "Failed to fetch")
  }
}

  useEffect(() => { refresh() }, [])

  const save = async () => {
    setBusy(true); setErr(null)
    try {
      await fetch(`${apiBase}/posts`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      })
      setForm({ title: "", site: "", grade: "", fte: 1.0, status: "ACTIVE_ROSTERABLE" })
      await refresh()
    } catch (e: any) {
      setErr(e?.message ?? String(e))
    } finally {
      setBusy(false)
    }
  }

  const addVacancyFromToday = async (postId: number) => {
    setBusy(true); setErr(null)
    try {
      const today = new Date().toISOString().slice(0,10)
      await fetch(`${apiBase}/posts/${postId}/vacancy`, {
        method: "POST",
        headers: { "Content-Type":"application/json" },
        body: JSON.stringify({ status: "VACANT_UNROSTERABLE", start_date: today })
      })
      await refresh()
    } catch (e: any) {
      setErr(e?.message ?? String(e))
    } finally {
      setBusy(false)
    }
  }

  return (
    <section style={{display:"grid", gap:"1rem"}}>
      <h2>Admin · Post Builder</h2>

      {err && <div style={{color:"crimson"}}>Error: {err}</div>}
      {busy && <div>Working…</div>}

      <div style={{display:"grid", gap:"0.5rem", maxWidth:560}}>
        <input placeholder="Title" value={form.title ?? ""} onChange={e=>setForm({...form, title:e.target.value})}/>
        <input placeholder="Site" value={form.site ?? ""} onChange={e=>setForm({...form, site:e.target.value})}/>
        <input placeholder="Grade" value={form.grade ?? ""} onChange={e=>setForm({...form, grade:e.target.value})}/>
        <input placeholder="FTE (0.1–1.0)" type="number" step="0.1" value={form.fte ?? 1.0}
               onChange={e=>setForm({...form, fte: parseFloat(e.target.value)})}/>
        <select value={form.status ?? "ACTIVE_ROSTERABLE"} onChange={e=>setForm({...form, status: e.target.value as Post["status"]})}>
          <option>ACTIVE_ROSTERABLE</option>
          <option>VACANT_ROSTERABLE</option>
          <option>VACANT_UNROSTERABLE</option>
        </select>
        <button onClick={save} disabled={busy || !form.title}>Save Post</button>
      </div>

      <div>
        <h3>Posts</h3>
        <ul>
          {posts.map(p => (
            <li key={p.id} style={{marginBottom:"0.4rem"}}>
              <strong>{p.title}</strong> · {p.site ?? "—"} · {p.grade ?? "—"} · FTE {p.fte} · <em>{p.status}</em>{" "}
              <button onClick={()=>addVacancyFromToday(p.id)} disabled={busy}>Mark Unrosterable (from today)</button>
            </li>
          ))}
        </ul>
      </div>
    </section>
  )
}
