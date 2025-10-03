import React, { useEffect, useState } from "react"

type CallPolicy = {
  participates_in_call: boolean
  max_nights_per_month: number
  min_rest_hours: number
  role: string
}
type Post = {
  id: number
  title: string
  site?: string | null
  grade?: string | null
  fte: number
  status: string
  call_policy: CallPolicy
}
type Props = { apiBase: string }

async function jsonFetch(url: string, init?: RequestInit) {
  const r = await fetch(url, {
    headers: { Accept: "application/json", ...(init?.headers || {}) },
    ...init,
  })
  const ct = r.headers.get("content-type") || ""
  const text = await r.text()
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}: ${text.slice(0,200)}`)
  if (!ct.includes("application/json")) throw new Error(`Non-JSON: ${text.slice(0,80)}`)
  return JSON.parse(text)
}

export default function AdminPostBuilder({ apiBase }: Props) {
  const [posts, setPosts] = useState<Post[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // create form
  const [title, setTitle] = useState("")
  const [site, setSite] = useState("")
  const [grade, setGrade] = useState("")
  const [fte, setFte] = useState("1.0")
  const [status, setStatus] = useState("ACTIVE_ROSTERABLE")
  const [participates, setParticipates] = useState(true)
  const [maxNights, setMaxNights] = useState(7)
  const [minRest, setMinRest] = useState(11)

  // edit state
  const [editingId, setEditingId] = useState<number | null>(null)
  const [edit, setEdit] = useState<Partial<Post>>({})

  const refresh = async () => {
    setLoading(true); setError(null)
    try {
      const data = await jsonFetch(`${apiBase}/posts`)
      setPosts(data)
    } catch (e: any) {
      setError(e.message || "Failed to fetch posts")
    } finally { setLoading(false) }
  }
  useEffect(() => { refresh() }, [])

  const saveNew = async () => {
    setError(null)
    try {
      await jsonFetch(`${apiBase}/posts`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: title.trim(),
          site: site.trim() || null,
          grade: grade.trim() || null,
          fte: Number(fte) || 1.0,
          status,
          call_policy: {
            participates_in_call: participates,
            max_nights_per_month: Number(maxNights) || 7,
            min_rest_hours: Number(minRest) || 11,
            role: "NCHD"
          }
        })
      })
      setTitle(""); setSite(""); setGrade(""); setFte("1.0"); setStatus("ACTIVE_ROSTERABLE")
      setParticipates(true); setMaxNights(7); setMinRest(11)
      refresh()
    } catch (e:any) { setError(e.message || "Failed to save post") }
  }

  const beginEdit = (p: Post) => {
    setEditingId(p.id)
    setEdit({
      id: p.id,
      title: p.title,
      site: p.site || "",
      grade: p.grade || "",
      fte: p.fte,
      status: p.status,
      call_policy: { ...p.call_policy }
    })
  }
  const cancelEdit = () => { setEditingId(null); setEdit({}) }

  const saveEdit = async () => {
    if (!editingId) return
    const payload: any = {
      title: (edit.title || "").trim(),
      site: (edit.site as string || "").trim() || null,
      grade: (edit.grade as string || "").trim() || null,
      fte: Number(edit.fte ?? 1.0),
      status: edit.status || "ACTIVE_ROSTERABLE",
      call_policy: edit.call_policy || {
        participates_in_call: true,
        max_nights_per_month: 7,
        min_rest_hours: 11,
        role: "NCHD"
      }
    }
    try {
      await jsonFetch(`${apiBase}/posts/${editingId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      })
      cancelEdit()
      refresh()
    } catch (e:any) { setError(e.message || "Failed to update post") }
  }

  return (
    <section style={{ display:"grid", gap:"1rem", maxWidth:900 }}>
      <h2>Admin · Post Builder</h2>

      {error && <div style={{background:"#fee",border:"1px solid #f99",padding:"8px"}}><b>Error:</b> {error}</div>}

      {/* Create */}
      <fieldset style={{padding:"8px"}}>
        <legend>Create Post</legend>
        <div style={{display:"grid",gridTemplateColumns:"2fr 1fr 1fr 1fr 1fr",gap:"8px",alignItems:"end"}}>
          <label>Title<br/><input value={title} onChange={e=>setTitle(e.target.value)} placeholder="Newcastle NCHD #1" /></label>
          <label>Site<br/><input value={site} onChange={e=>setSite(e.target.value)} placeholder="Newcastle" /></label>
          <label>Grade<br/><input value={grade} onChange={e=>setGrade(e.target.value)} placeholder="Registrar" /></label>
          <label>FTE<br/><input value={fte} onChange={e=>setFte(e.target.value)} /></label>
          <label>Status<br/>
            <select value={status} onChange={e=>setStatus(e.target.value)}>
              <option>ACTIVE_ROSTERABLE</option>
              <option>VACANT_UNROSTERABLE</option>
            </select>
          </label>
        </div>

        <div style={{display:"grid",gridTemplateColumns:"1fr 1fr 1fr 1fr",gap:"8px",marginTop:8}}>
          <label><input type="checkbox" checked={participates} onChange={e=>setParticipates(e.target.checked)} /> Participates in call</label>
          <label>Max nights / month<br/><input type="number" value={maxNights} onChange={e=>setMaxNights(parseInt(e.target.value||"0"))} /></label>
          <label>Min rest (h)<br/><input type="number" value={minRest} onChange={e=>setMinRest(parseInt(e.target.value||"0"))} /></label>
          <div><button disabled={!title.trim()} onClick={saveNew}>Save Post</button></div>
        </div>
      </fieldset>

      {/* List + Edit */}
      <h3>Posts</h3>
      {loading ? <div>Loading…</div> : (
        <table style={{width:"100%",borderCollapse:"collapse"}}>
          <thead>
            <tr>
              <th style={{textAlign:"left"}}>Title</th>
              <th>Site</th><th>Grade</th><th>FTE</th><th>Status</th>
              <th>Participates</th><th>Max nights</th><th>Min rest</th><th></th>
            </tr>
          </thead>
          <tbody>
            {posts.map(p => {
              const editing = editingId === p.id
              return (
                <tr key={p.id}>
                  <td style={{borderTop:"1px solid #ddd"}}>
                    {editing ? <input value={String(edit.title||"")} onChange={e=>setEdit({...edit, title:e.target.value})}/> : <b>{p.title}</b>}
                  </td>
                  <td style={{borderTop:"1px solid #ddd"}}>
                    {editing ? <input value={String(edit.site||"")} onChange={e=>setEdit({...edit, site:e.target.value})}/> : (p.site||"—")}
                  </td>
                  <td style={{borderTop:"1px solid #ddd"}}>
                    {editing ? <input value={String(edit.grade||"")} onChange={e=>setEdit({...edit, grade:e.target.value})}/> : (p.grade||"—")}
                  </td>
                  <td style={{borderTop:"1px solid #ddd"}}>
                    {editing ? <input value={String(edit.fte??1)} onChange={e=>setEdit({...edit, fte:Number(e.target.value||"1")})}/> : p.fte}
                  </td>
                  <td style={{borderTop:"1px solid #ddd"}}>
                    {editing ? (
                      <select value={String(edit.status||"ACTIVE_ROSTERABLE")} onChange={e=>setEdit({...edit, status:e.target.value})}>
                        <option>ACTIVE_ROSTERABLE</option>
                        <option>VACANT_UNROSTERABLE</option>
                      </select>
                    ) : <em>{p.status}</em>}
                  </td>
                  <td style={{borderTop:"1px solid #ddd", textAlign:"center"}}>
                    {editing ? (
                      <input type="checkbox"
                        checked={!!(edit.call_policy as any)?.participates_in_call}
                        onChange={e=>setEdit({
                          ...edit,
                          call_policy: {...(edit.call_policy||p.call_policy), participates_in_call: e.target.checked}
                        })}
                      />
                    ) : (p.call_policy?.participates_in_call ? "Yes" : "No")}
                  </td>
                  <td style={{borderTop:"1px solid #ddd"}}>
                    {editing ? (
                      <input type="number"
                        value={(edit.call_policy as any)?.max_nights_per_month ?? p.call_policy?.max_nights_per_month ?? 7}
                        onChange={e=>setEdit({
                          ...edit,
                          call_policy: {...(edit.call_policy||p.call_policy), max_nights_per_month: parseInt(e.target.value||"0")}
                        })}
                      />
                    ) : (p.call_policy?.max_nights_per_month ?? 7)}
                  </td>
                  <td style={{borderTop:"1px solid #ddd"}}>
                    {editing ? (
                      <input type="number"
                        value={(edit.call_policy as any)?.min_rest_hours ?? p.call_policy?.min_rest_hours ?? 11}
                        onChange={e=>setEdit({
                          ...edit,
                          call_policy: {...(edit.call_policy||p.call_policy), min_rest_hours: parseInt(e.target.value||"0")}
                        })}
                      />
                    ) : (p.call_policy?.min_rest_hours ?? 11)}
                  </td>
                  <td style={{borderTop:"1px solid #ddd"}}>
                    {editing ? (
                      <>
                        <button onClick={saveEdit}>Save</button>
                        <button onClick={cancelEdit} style={{marginLeft:8}}>Cancel</button>
                      </>
                    ) : (
                      <button onClick={()=>beginEdit(p)}>Edit</button>
                    )}
                  </td>
                </tr>
              )
            })}
            {posts.length === 0 && (
              <tr><td colSpan={9} style={{padding:"8px"}}>No posts yet.</td></tr>
            )}
          </tbody>
        </table>
      )}
    </section>
  )
}
