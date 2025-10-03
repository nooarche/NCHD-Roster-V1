import React, { useEffect, useState } from "react"

type Group = {
  id: number
  name: string
  kind: string   // "on_call_pool" | "teaching_block" | "team" | ...
  rules?: any
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
  if (!ct.includes("application/json")) throw new Error(`Non-JSON: ${text.slice(0,120)}`)
  return JSON.parse(text)
}

export default function AdminGroups({ apiBase }: Props) {
  const [groups, setGroups] = useState<Group[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // create form
  const [name, setName] = useState("")
  const [kind, setKind] = useState<"on_call_pool"|"teaching_block"|"team">("on_call_pool")
  const [rulesText, setRulesText] = useState<string>('{}')

  // edit row
  const [editingId, setEditingId] = useState<number | null>(null)
  const [editName, setEditName] = useState("")
  const [editKind, setEditKind] = useState<"on_call_pool"|"teaching_block"|"team">("on_call_pool")
  const [editRulesText, setEditRulesText] = useState<string>('{}')

  const refresh = async () => {
    setLoading(true); setError(null)
    try {
      const data = await jsonFetch(`${apiBase}/groups`)
      setGroups(Array.isArray(data) ? data : [])
    } catch (e:any) {
      setError(e.message || "Failed to load groups")
    } finally { setLoading(false) }
  }

  useEffect(() => { refresh() }, []) // eslint-disable-line

  const parseJSONSafe = (txt: string) => {
    try { return JSON.parse(txt) } catch { return {} }
  }

  const createGroup = async () => {
    setError(null)
    try {
      await jsonFetch(`${apiBase}/groups`, {
        method: "POST",
        headers: { "Content-Type":"application/json" },
        body: JSON.stringify({ name: name.trim(), kind, rules: parseJSONSafe(rulesText) })
      })
      setName(""); setKind("on_call_pool"); setRulesText('{}')
      refresh()
    } catch (e:any) {
      setError(e.message || "Failed to create group")
    }
  }

  const startEdit = (g: Group) => {
    setEditingId(g.id)
    setEditName(g.name)
    setEditKind((g.kind as any) || "on_call_pool")
    setEditRulesText(JSON.stringify(g.rules || {}, null, 2))
  }

  const cancelEdit = () => {
    setEditingId(null)
    setEditName(""); setEditKind("on_call_pool"); setEditRulesText("{}")
  }

  const saveEdit = async () => {
    if (!editingId) return
    setError(null)
    try {
      await jsonFetch(`${apiBase}/groups/${editingId}`, {
        method: "PUT",
        headers: { "Content-Type":"application/json" },
        body: JSON.stringify({ name: editName.trim(), kind: editKind, rules: parseJSONSafe(editRulesText) })
      })
      cancelEdit()
      refresh()
    } catch (e:any) {
      setError(e.message || "Failed to update group")
    }
  }

  const removeGroup = async (id: number) => {
    if (!confirm("Delete this group?")) return
    setError(null)
    try {
      await jsonFetch(`${apiBase}/groups/${id}`, { method: "DELETE" })
      refresh()
    } catch (e:any) {
      setError(e.message || "Failed to delete group")
    }
  }

  return (
    <section style={{ display:"grid", gap:12, maxWidth:1000 }}>
      <h2>Admin · Groups</h2>

      {error && (
        <div style={{ background:"#fee", border:"1px solid #f99", padding:8 }}>
          <strong>Error:</strong> {error}
        </div>
      )}

      <fieldset style={{ padding:12, border:"1px solid #ddd" }}>
        <legend>Create Group</legend>
        <div style={{ display:"grid", gridTemplateColumns:"2fr 1fr 1fr", gap:8, alignItems:"end" }}>
          <label>Name<br/><input value={name} onChange={e=>setName(e.target.value)} placeholder="Newcastle 24h Pool" /></label>
          <label>Kind<br/>
            <select value={kind} onChange={e=>setKind(e.target.value as any)}>
              <option value="on_call_pool">on_call_pool</option>
              <option value="teaching_block">teaching_block</option>
              <option value="team">team</option>
            </select>
          </label>
          <button onClick={createGroup} disabled={!name.trim()}>Create</button>
        </div>
        <label style={{ marginTop:8, display:"block" }}>Rules (JSON)<br/>
          <textarea rows={6} value={rulesText} onChange={e=>setRulesText(e.target.value)} style={{ width:"100%" }} />
        </label>
        <div style={{ fontSize:12, color:"#666", marginTop:4 }}>
          Examples:<br/>
          <code>{`{"shift":"night","hours":[["17:00","09:00"]]}`}</code> (on-call pool)<br/>
          <code>{`{"weekday":"Wed","time":["14:00","16:00"]}`}</code> (teaching block)<br/>
          <code>{`{"clinic_days":["Mon","Thu"],"supervision":{"weekday":"Tue","time":["10:00","11:00"]}}`}</code> (team)
        </div>
      </fieldset>

      <h3>Groups</h3>

      {loading ? <div>Loading…</div> : (
        <table style={{ width:"100%", borderCollapse:"collapse" }}>
          <thead>
            <tr>
              <th style={{ textAlign:"left" }}>Name</th>
              <th>Kind</th>
              <th>Rules</th>
              <th style={{ width:180 }}></th>
            </tr>
          </thead>
          <tbody>
            {groups.map(g => {
              const editing = editingId === g.id
              return (
                <tr key={g.id}>
                  <td style={{ borderTop:"1px solid #ddd" }}>
                    {editing
                      ? <input value={editName} onChange={e=>setEditName(e.target.value)} />
                      : <strong>{g.name}</strong>}
                  </td>
                  <td style={{ borderTop:"1px solid #ddd" }}>
                    {editing
                      ? (
                        <select value={editKind} onChange={e=>setEditKind(e.target.value as any)}>
                          <option value="on_call_pool">on_call_pool</option>
                          <option value="teaching_block">teaching_block</option>
                          <option value="team">team</option>
                        </select>
                      )
                      : <em>{g.kind}</em>}
                  </td>
                  <td style={{ borderTop:"1px solid #ddd", maxWidth:400 }}>
                    {editing
                      ? <textarea rows={5} value={editRulesText} onChange={e=>setEditRulesText(e.target.value)} style={{ width:"100%" }} />
                      : <code style={{ fontSize:12, whiteSpace:"pre-wrap" }}>{JSON.stringify(g.rules || {}, null, 0)}</code>}
                  </td>
                  <td style={{ borderTop:"1px solid #ddd" }}>
                    {editing ? (
                      <>
                        <button onClick={saveEdit}>Save</button>
                        <button onClick={cancelEdit} style={{ marginLeft:8 }}>Cancel</button>
                      </>
                    ) : (
                      <>
                        <button onClick={()=>startEdit(g)}>Edit</button>
                        <button onClick={()=>removeGroup(g.id)} style={{ marginLeft:8 }}>Delete</button>
                      </>
                    )}
                  </td>
                </tr>
              )
            })}
            {groups.length === 0 && !loading && (
              <tr><td colSpan={4} style={{ padding:8 }}>No groups yet.</td></tr>
            )}
          </tbody>
        </table>
      )}
    </section>
  )
}
