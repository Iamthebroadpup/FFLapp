import { PlayerScore } from "../types";


type Props = {
  rows: PlayerScore[];
  onDraft: (id:number)=>void;
  onAssign: (id:number, teamIndex:number)=>void;
  drafted: Set<number>;
  taken: Set<number>;
  teams: number;
  teamNames?: string[];
  loading?: boolean;
}

export default function PlayerTable({rows, onDraft, onAssign, drafted, taken, teams, teamNames, loading}: Props){
  const list = Array.isArray(rows) ? rows : [];
  return (
    <div className="bg-white rounded-2xl shadow overflow-hidden">
      <div className="overflow-auto">
        <table className="min-w-full text-sm">
          <thead className="bg-gray-100 text-gray-700 sticky top-0">
            <tr>
              <th className="text-left p-2">#</th>
              <th className="text-left p-2">Player</th>
              <th className="text-left p-2">Pos</th>
              <th className="text-right p-2">Proj</th>
              <th className="text-right p-2">VORP</th>
              <th className="text-right p-2">ADP</th>
              <th className="text-right p-2">Δ Rank vs ADP</th>
              <th className="p-2"></th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={8} className="p-4 text-center">Loading…</td></tr>
            ) : list.length===0 ? (
              <tr><td colSpan={8} className="p-4 text-center text-gray-500">No players</td></tr>
            ) : list.map((r,i)=>(
              <tr key={r.player.player_id} className={(drafted.has(r.player.player_id)||taken.has(r.player.player_id))?'bg-gray-50 text-gray-400':''}>
                <td className="p-2">{i+1}</td>
                <td className="p-2">{r.player.name} <span className="text-gray-400">({r.player.team})</span></td>
                <td className="p-2">{r.player.position}</td>
                <td className="p-2 text-right">{r.points.toFixed(1)}</td>
                <td className="p-2 text-right">{r.vorp.toFixed(1)}</td>
                <td className="p-2 text-right">{r.player.adp ?? r.player.adp_ppr ?? '—'}</td>
                <td className="p-2 text-right">{r.value_vs_adp !== null && r.value_vs_adp !== undefined ? r.value_vs_adp.toFixed(1) : '—'}</td>
                <td className="p-2 text-right">
                  <div className="flex gap-2 justify-end">
                    <button
                      disabled={drafted.has(r.player.player_id) || taken.has(r.player.player_id)}
                      onClick={()=>onDraft(r.player.player_id)}
                      className={`px-3 py-1 rounded ${(drafted.has(r.player.player_id)||taken.has(r.player.player_id))?'bg-gray-200':'bg-black text-white'}`}
                    >
                      Draft
                    </button>
                    <div className="flex items-center gap-1">
                      <select className="border rounded px-1 py-1 text-xs" onChange={(e)=>onAssign(r.player.player_id, Number(e.target.value))} defaultValue={0}>
                        <option value={0}>Assign…</option>
                        {Array.from({length: teams}).map((_,idx)=>(
                          <option key={idx+1} value={idx+1}>{teamNames?.[idx] || `Team ${idx+1}`}</option>
                        ))}
                      </select>
                    </div>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
