import React from 'react'
import { Player } from '../types'

function fmt(v: any, digits = 1) {
  if (typeof v === 'number' && Number.isFinite(v)) return v.toFixed(digits);
  const n = Number(v);
  return Number.isFinite(n) ? n.toFixed(digits) : '-';
}

export default function PlayerList({ players, onDraft }: { players: Player[], onDraft: (p: Player, team: string)=>void }) {
  return (
    <div className="list">
      {players.map(p => (
        <div key={p.player_id} className="player-card"
          draggable
          onDragStart={e=>{
            e.dataTransfer.setData('application/x-player-id', String(p.player_id))
            e.dataTransfer.setData('text/plain', p.name)
          }}>
          <div>
            <div style={{fontWeight:700}}>{p.name}</div>
            <div className="badge">{p.team} • {p.position} • Bye {p.bye_week ?? '-'}</div>
            <div className="badge">ADP {fmt(p.adp)} • Proj {fmt(p.projected_points)}</div>
            {p.depth_order ? <div className="badge">Depth {p.depth_order} • Comm {p.committee_size || '-'}</div> : null}
          </div>
          <div style={{textAlign:'right'}}>{fmt(p.projected_points)}</div>
          <button onClick={()=>onDraft(p, 'ME')}>Draft</button>
          <button onClick={()=>onDraft(p, 'OTHER')}>Other</button>
        </div>
      ))}
    </div>
  )
}
