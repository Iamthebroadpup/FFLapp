import { LeagueConfig } from "../types";
import { useState } from "react";

type Props = {
  cfg: LeagueConfig;
  setCfg: (c: LeagueConfig)=>void;
  onInit: (year: number, type: 'REG'|'PRE'|'POST')=>void;
}

export default function SettingsBar({cfg, setCfg, onInit}: Props){
  const [year, setYear] = useState(cfg.season_year);
  const [stype, setStype] = useState<'REG'|'PRE'|'POST'>(cfg.season_type);

  return (
    <div className="flex flex-wrap items-center gap-3 p-3 bg-white rounded-2xl shadow">
      <div className="flex items-center gap-2">
        <label className="text-sm font-medium">Season</label>
        <input type="number" value={year} onChange={e=>setYear(Number(e.target.value))}
          className="px-2 py-1 border rounded w-24" />
        <select value={stype} onChange={e=>setStype(e.target.value as any)} className="px-2 py-1 border rounded">
          <option value="REG">REG</option><option value="PRE">PRE</option><option value="POST">POST</option>
        </select>
        <button onClick={()=>onInit(year,stype)} className="px-3 py-1 rounded bg-black text-white">Load</button>
      </div>

      <div className="w-px h-6 bg-gray-200"/>

      <div className="flex items-center gap-2">
        <label className="text-sm font-medium">Teams</label>
        <input type="number" min={4} max={20}
          value={cfg.teams} onChange={e=>setCfg({...cfg, teams:Number(e.target.value)})}
          className="px-2 py-1 border rounded w-20" />
      </div>

      <div className="flex items-center gap-2">
        <label className="text-sm font-medium">Scoring</label>
        <select
          value={cfg.scoring.rec===0.5?'HALF':(cfg.scoring.rec===1?'PPR':'STD')}
          onChange={e=>{
            const mode = e.target.value;
            const rec = mode==='PPR'?1: mode==='HALF'?0.5:0;
            setCfg({...cfg, scoring:{...cfg.scoring, rec}});
          }}
          className="px-2 py-1 border rounded"
        >
          <option value="STD">Standard</option>
          <option value="HALF">Half-PPR</option>
          <option value="PPR">PPR</option>
        </select>
      </div>

      <div className="flex items-center gap-2">
        <label className="text-sm">Roster</label>
        <div className="flex items-center gap-1 text-xs">
          {["QB","RB","WR","TE","FLEX","DST","K"].map(pos=>(
            <span key={pos} className="flex items-center gap-1">
              {pos}
              <input type="number" className="w-12 px-1 py-0.5 border rounded"
                value={cfg.roster[pos] ?? 0}
                onChange={e=>setCfg({...cfg, roster:{...cfg.roster, [pos]: Number(e.target.value)}})}
              />
            </span>
          ))}
        </div>
      </div>
    </div>
  )
}
