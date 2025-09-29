import React from "react"

export type AdminTab = "Users" | "Posts" | "Teams" | "Contracts" | "On-call" | "Core Hours" | "OPD" | "Supervision"

export function AdminNav({active, onChange}:{active:AdminTab; onChange:(t:AdminTab)=>void}) {
  const tabs: AdminTab[] = ["Users","Posts","Teams","Contracts","On-call","Core Hours","OPD","Supervision"]
  return (
    <div style={{display:"flex", gap:8, flexWrap:"wrap", marginBottom:12}}>
      {tabs.map(t => (
        <button key={t} onClick={()=>onChange(t)}
          style={{padding:"6px 10px", border:"1px solid #ddd", borderRadius:6,
                  background: t===active ? "#f5f5f5" : "white", fontWeight: t===active ? 700 : 500}}>
          {t}
        </button>
      ))}
    </div>
  )
}
