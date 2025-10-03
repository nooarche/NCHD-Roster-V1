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
  core_hours?: any
  eligibility?: any
  notes?: string | null
  call_policy?: CallPolicy
  group_ids?: number[]
}

type Group = { id: number; name: string; kind: string; rules?: any }

type Props = { apiBase: string }

async function jsonFetch(url: string, init?: RequestInit) {
  const r = await fetch(url, {
    headers: { Accept: "application/json", ...(init?.headers || {}) },
    ...init,
  })
  const ct = r.headers.get("content-type") || ""
  const bodyText = await r.text()
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}: ${bodyText.slice(0, 400)}`)
  if (!ct.includes("application/json")) throw new Error(`Non-JSON response: ${bodyText.slice(0, 120)}`)
  return JSON.parse(bodyText)
}

export default function AdminPostBuilder({ apiBase }: Props) {
  // data
  const [posts, setPosts] = useState<Post[]>([])
  const [groups, setGroups] = useState<Group[]>([])

  // ui state
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // create form state
  const [title, setTitle] = useState("")
  const [site, setSite] = useState("")
  const [grade, setGrade] = useState("")
  const [fte, setFte] = useState("1.0")
  const [status, setStatus] = useState("ACTIVE_ROSTERABLE")
  const [coreHoursText, setCoreHoursText] = useState<string>('{"Mon":[["09:00","17:00"]]}')
  const [selectedGroupIds, setSelectedGroupIds] = useState<number[]>([])
  // call policy (optional now; you can enable later in payload)
  const [participates, setParticipates] = useState(true)
  const [maxNights, setMaxNights] = useState(7)
  const [minRest, setMinRest] = useState(11)

  // edit row state
  const [editingId, setEditingId] = useState<number | null>(null)
  const [edit, setEdit] = useState<Partial<Post>>({})
  const [editCoreHoursText, setEditCoreHoursText] = useState<string>("")
  const [editGroupIds, setEditGroupIds] = useState<number[]>([])

  // ---------- load ----------
  const refresh = async () => {
    setLoading(true)
    setError(null)
    try {
      const ps = await jsonFetch(`${apiBase}/posts`)
      setPosts(Array.isArray(ps) ? ps : [])
    } catch (e: any) {
      setError(e.message || "Failed to load posts")
    } finally {
      setLoading(false)
    }

    // Groups are optional; don’t fail the whole screen if they 404
    try {
      const gs = await jsonFetch(`${apiBase}/groups`)
      setGroups(Array.isArray(gs) ? gs : [])
    } catch {
      setGroups([])
    }
  }

  useEffect(() => { refresh() }, []) // eslint-disable-line

  // ---------- helpers ----------
  const parseJSONSafe = (txt: string) => {
    try { return JSON.parse(txt) } catch { return {} }
  }

  // ---------- create ----------
  const saveNew = async () => {
    setError(null)
    const payload: any = {
      title: title.trim(),
      site: site.trim() || null,
      grade: grade.trim() || null,
      fte: Number(fte) || 1.0,
      status,
      core_hours: parseJSONSafe(coreHoursText),
      group_ids: selectedGroupIds,
      // enable later if/when you want call policy persisted here:
      // call_policy: {
      //   participates_in_call: participates,
      //   max_nights_per_month: Number(maxNights) || 7,
      //   min_rest_hours: Number(minRest) || 11,
      //   role: "NCHD"
      // }
    }

    try {
      await jsonFetch(`${apiBase}/posts`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify(payload),
      })
      // reset form
      setTitle(""); setSite(""); setGrade(""); setFte("1.0"); setStatus("ACTIVE_ROSTERABLE")
      setCoreHoursText('{"Mon":[["09:00","17:00"]]}')
      setSelectedGroupIds([])
      setParticipates(true); setMaxNights(7); setMinRest(11)
      refresh()
    } catch (e: any) {
      setError(e.message || "Failed to save post")
    }
  }

  // ---------- edit ----------
  const beginEdit = (p: Post) => {
    setEditingId(p.id)
    setEdit({
      id: p.id,
      title: p.title,
      site: p.site || "",
      grade: p.grade || "",
      fte: p.fte ?? 1,
      status: p.status || "ACTIVE_ROSTERABLE",
      call_policy: p.call_policy || {
        participates_in_call: true, max_nights_per_month: 7, min_rest_hours: 11, role: "NCHD"
      }
    })
    setEditCoreHoursText(JSON.stringify(p.core_hours || {}, null, 2))
    setEditGroupIds(p.group_ids || [])
  }

  const cancelEdit = () => {
    setEditingId(null)
    setEdit({})
    setEditCoreHoursText("")
    setEditGroupIds([])
  }

  const saveEdit = async () => {
    if (!editingId) return
    setError(null)
    const payload: any = {
      title: (edit.title || "").toString().trim(),
      site: (edit.site as string || "").trim() || null,
      grade: (edit.grade as string || "").trim() || null,
      fte: Number(edit.fte ?? 1),
      status: edit.status || "ACTIVE_ROSTERABLE",
      core_hours: parseJSONSafe(editCoreHoursText),
      group_ids: editGroupIds,
      // include if you want to persist call policy now:
      // call_policy: edit.call_policy
    }

    try {
      await jsonFetch(`${apiBase}/posts/${editingId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify(payload),
      })
      cancelEdit()
      refresh()
    } catch (e: any) {
      setError(e.message || "Failed to update post")
    }
  }

  // ---------- render ----------
  return (
    <section style={{ display: "grid", gap: "1rem", maxWidth: 1000 }}>
      <h2>Admin · Post Builder</h2>

      {error && (
        <div style={{ background: "#fee", border: "1px solid #f99", padding: "8px" }}>
          <strong>Error:</strong> {error}
        </div>
      )}

      {/* Create Post */}
      <fieldset style={{ padding: 12, border: "1px solid #ddd" }}>
        <legend>Create Post</legend>

        <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr 1fr 1fr 1fr", gap: 8, alignItems: "end" }}>
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

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8, marginTop: 8 }}>
          <label>Core hours (JSON)<br/>
            <textarea rows={6} value={coreHoursText} onChange={e=>setCoreHoursText(e.target.value)} />
          </label>

          <div>
            <label>Assign to groups<br/>
              <select multiple value={selectedGroupIds.map(String)} onChange={e=>{
                const vals = Array.from(e.target.selectedOptions).map(o => Number(o.value))
                setSelectedGroupIds(vals)
              }} style={{ width: "100%", minHeight: 120 }}>
                {groups.map(g => <option key={g.id} value={g.id}>{g.name} · {g.kind}</option>)}
              </select>
            </label>

            {/* Optional: quick call-policy fields (not sent unless you uncomment above) */}
            <div style={{ marginTop: 12, display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 8 }}>
              <label><input type="checkbox" checked={participates} onChange={e=>setParticipates(e.target.checked)} /> Participates in call</label>
              <label>Max nights/month<br/><input type="number" value={maxNights} onChange={e=>setMaxNights(parseInt(e.target.value || "0"))} /></label>
              <label>Min rest (h)<br/><input type="number" value={minRest} onChange={e=>setMinRest(parseInt(e.target.value || "0"))} /></label>
            </div>
          </div>
        </div>

        <div style={{ marginTop: 10 }}>
          <button onClick={saveNew} disabled={!title.trim()}>Save Post</button>
        </div>
      </fieldset>

      {/* List + Inline Edit */}
      <h3>Posts</h3>
      {loading ? (
        <div>Loading…</div>
      ) : (
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr>
              <th style={{ textAlign: "left" }}>Title</th>
              <th>Site</th>
              <th>Grade</th>
              <th>FTE</th>
              <th>Status</th>
              <th>Groups</th>
              <th>Core hours</th>
              <th style={{ width: 150 }}></th>
            </tr>
          </thead>
          <tbody>
            {posts.map(p => {
              const editing = editingId === p.id
              return (
                <tr key={p.id}>
                  <td style={{ borderTop: "1px solid #ddd" }}>
                    {editing
                      ? <input value={String(edit.title ?? "")} onChange={e=>setEdit({ ...edit, title: e.target.value })} />
                      : <strong>{p.title}</strong>}
                  </td>
                  <td style={{ borderTop: "1px solid #ddd" }}>
                    {editing
                      ? <input value={String(edit.site ?? "")} onChange={e=>setEdit({ ...edit, site: e.target.value })} />
                      : (p.site || "—")}
                  </td>
                  <td style={{ borderTop: "1px solid #ddd" }}>
                    {editing
                      ? <input value={String(edit.grade ?? "")} onChange={e=>setEdit({ ...edit, grade: e.target.value })} />
                      : (p.grade || "—")}
                  </td>
                  <td style={{ borderTop: "1px solid #ddd" }}>
                    {editing
                      ? <input value={String(edit.fte ?? 1)} onChange={e=>setEdit({ ...edit, fte: Number(e.target.value || "1") })} />
                      : p.fte}
                  </td>
                  <td style={{ borderTop: "1px solid #ddd" }}>
                    {editing ? (
                      <select value={String(edit.status || "ACTIVE_ROSTERABLE")} onChange={e=>setEdit({ ...edit, status: e.target.value })}>
                        <option>ACTIVE_ROSTERABLE</option>
                        <option>VACANT_UNROSTERABLE</option>
                      </select>
                    ) : <em>{p.status}</em>}
                  </td>

                  {/* Groups */}
                  <td style={{ borderTop: "1px solid #ddd" }}>
                    {editing ? (
                      <select multiple value={editGroupIds.map(String)} onChange={e=>{
                        const vals = Array.from(e.target.selectedOptions).map(o => Number(o.value))
                        setEditGroupIds(vals)
                      }} style={{ minWidth: 160, minHeight: 80 }}>
                        {groups.map(g => <option key={g.id} value={g.id}>{g.name} · {g.kind}</option>)}
                      </select>
                    ) : (
                      (p.group_ids || []).map(id => groups.find(g => g.id === id)?.name || `#${id}`).join(", ") || "—"
                    )}
                  </td>

                  {/* Core hours */}
                  <td style={{ borderTop: "1px solid #ddd", maxWidth: 260 }}>
                    {editing ? (
                      <textarea rows={5} value={editCoreHoursText} onChange={e=>setEditCoreHoursText(e.target.value)} style={{ width: "100%" }} />
                    ) : (
                      <code style={{ fontSize: 12, whiteSpace: "pre-wrap" }}>
                        {JSON.stringify(p.core_hours || {}, null, 0)}
                      </code>
                    )}
                  </td>

                  <td style={{ borderTop: "1px solid #ddd" }}>
                    {editing ? (
                      <>
                        <button onClick={saveEdit}>Save</button>
                        <button onClick={cancelEdit} style={{ marginLeft: 8 }}>Cancel</button>
                      </>
                    ) : (
                      <button onClick={() => beginEdit(p)}>Edit</button>
                    )}
                  </td>
                </tr>
              )
            })}
            {posts.length === 0 && (
              <tr><td colSpan={8} style={{ padding: 8 }}>No posts yet.</td></tr>
            )}
          </tbody>
        </table>
      )}
    </section>
  )
}
