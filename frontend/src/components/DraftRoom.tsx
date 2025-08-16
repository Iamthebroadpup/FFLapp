import { useMemo } from "react";
import { PlayerScore } from "../types";

type Props = {
  teams: number;
  teamNames: string[];
  setTeamNames: (n: string[]) => void;
  picks: number[];              // your picks (player_ids)
  others: [number, number][];   // [player_id, team_index]  (sanitized upstream)
  all: PlayerScore[];
  onAssign: (playerId: number, teamIndex: number) => void;
  onUndo: () => void;
  onClear: () => void;
};

export default function DraftRoom({
  teams, teamNames, setTeamNames, picks, others, all, onAssign, onUndo, onClear
}: Props) {

  const byId = useMemo(() => new Map(all.map(p => [p.player.player_id, p])), [all]);

  const columns = useMemo(() => {
    const cols: { teamIndex: number; name: string; rows: PlayerScore[] }[] = [];
    for (let i = 1; i <= teams; i++) {
      const ids = (i === 1 ? picks : []).concat(
        others.filter(o => Array.isArray(o) && o.length >= 2 && o[1] === i).map(o => o[0])
      );
      const rows = ids.map(id => byId.get(id)).filter(Boolean) as PlayerScore[];
      cols.push({ teamIndex: i, name: teamNames[i - 1] || `Team ${i}`, rows });
    }
    return cols;
  }, [teams, picks, others, byId, teamNames]);

  return (
    <div className="bg-white rounded-2xl shadow p-3 space-y-2">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold">Draft Room</h3>
        <div className="flex gap-2">
          <button onClick={onUndo} className="px-3 py-1 rounded bg-gray-200">Undo</button>
          <button onClick={onClear} className="px-3 py-1 rounded bg-red-600 text-white">Clear</button>
        </div>
      </div>

      {/* Auto-fit columns with a min width so headers don't get squished */}
      <div className="grid grid-cols-[repeat(auto-fit,minmax(220px,1fr))] gap-3">
        {columns.map(col => (
          <div key={col.teamIndex} className="rounded-lg border min-w-[220px]">
            <div className="px-2 py-2 border-b bg-gray-50 flex items-center gap-2">
              <input
                className="w-full px-2 py-1 rounded border bg-white text-sm md:text-base"
                value={col.name}
                title={col.name}               // full name on hover
                onChange={e => {
                  const copy = [...teamNames];
                  copy[col.teamIndex - 1] = e.target.value;
                  setTeamNames(copy);
                }}
              />
            </div>
            <ol className="text-sm space-y-1 max-h-72 overflow-auto p-2">
              {col.rows.map((r, idx) => (
                <li key={idx} className="flex justify-between bg-gray-50 rounded p-2">
                  <div>
                    {r.player.name}{" "}
                    <span className="text-gray-500">({r.player.team} • {r.player.position})</span>
                  </div>
                  <div className="text-xs text-gray-600">Proj {r.points.toFixed(1)}</div>
                </li>
              ))}
              {col.rows.length === 0 && <div className="text-gray-400">—</div>}
            </ol>
          </div>
        ))}
      </div>

      <div className="text-xs text-gray-500">
        Tip: Rename teams above. Use Assign… in the players table to mark other teams' picks.
      </div>
    </div>
  );
}
