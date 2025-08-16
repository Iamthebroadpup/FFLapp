import { Suggestion, LeagueConfig } from "../types";

type Props = {
  items: Suggestion[];
  refresh: ()=>void;
  cfg: LeagueConfig;
}

export default function SuggestPanel({items, refresh, cfg}: Props){
  return (
    <div className="bg-white rounded-2xl shadow p-3">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold">Suggestions</h3>
        <button className="px-3 py-1 rounded bg-black text-white" onClick={refresh}>Recompute</button>
      </div>
      <div className="mt-2 text-xs text-gray-600">
        <div>Teams: {cfg.teams} • Roster: QB{cfg.roster.QB} RB{cfg.roster.RB} WR{cfg.roster.WR} TE{cfg.roster.TE} FLEX{cfg.roster.FLEX} DST{cfg.roster.DST||0} K{cfg.roster.K||0} • Scoring: Rec = {cfg.scoring.rec}</div>
      </div>
      <ul className="mt-2 space-y-2">
        {items.slice(0,12).map(s=>(
          <li key={s.player_score.player.player_id} className="border rounded-lg p-2">
            <div className="flex justify-between">
              <div className="font-medium">{s.player_score.player.name} <span className="text-gray-500">({s.player_score.player.team} • {s.player_score.player.position})</span></div>
              <div className="text-sm">Proj {s.player_score.points.toFixed(1)} | VORP {s.player_score.vorp.toFixed(1)}</div>
            </div>
            <div className="text-xs text-gray-600">{s.reason}</div>
          </li>
        ))}
        {items.length===0 && <div className="text-sm text-gray-500">No suggestions yet.</div>}
      </ul>
    </div>
  )
}
