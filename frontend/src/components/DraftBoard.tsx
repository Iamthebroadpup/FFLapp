import React, { useMemo } from "react";
import { Player } from "../types";

type DraftedItem = { player: Player; teamName: string };

export default function DraftBoard({
  drafted,
  teamNames,
  onRenameTeam,
  onUndraft,
  onDrop,
}: {
  drafted: DraftedItem[];
  teamNames: string[];
  onRenameTeam: (index: number, name: string) => void;
  onUndraft: (p: Player) => void;
  onDrop: (p: Player, team: string) => void;
}) {
  const grouped = useMemo(() => {
    const map = new Map<string, DraftedItem[]>();
    teamNames.forEach((t) => map.set(t, []));
    drafted.forEach((d) => {
      if (!map.has(d.teamName)) map.set(d.teamName, []);
      map.get(d.teamName)!.push(d);
    });
    return teamNames.map((name) => ({ name, items: map.get(name) || [] }));
  }, [drafted, teamNames]);

  const prevent = (e: React.DragEvent) => e.preventDefault();
  const onDropTo = (e: React.DragEvent, team: string) => {
    e.preventDefault();
    const id = Number(e.dataTransfer.getData("application/x-player-id"));
    const name = e.dataTransfer.getData("text/plain") || "";
    if (!id) return;
    onDrop({ player_id: id, name, position: "", team: "" } as any, team);
  };

  return (
    <div>
      <h3>Draft Board</h3>
      <div className="teams-stack">
        {grouped.map((col, idx) => (
          <div
            key={idx}
            className="team-row"
            onDragOver={prevent}
            onDrop={(e) => onDropTo(e, col.name)}
          >
            <input
              className="team-name-input"
              value={col.name}
              onChange={(e) => onRenameTeam(idx, e.target.value)}
              title="Rename team"
            />

            <div className="row-scroll">
              {col.items.map((d) => (
                <div key={d.player.player_id} className="player-chip">
                  <div className="name" title={d.player.name}>{d.player.name}</div>
                  <div className="meta">
                    {d.player.team || "-"} • {d.player.position || "-"} • Bye {d.player.bye_week || "-"}
                  </div>
                  <button onClick={() => onUndraft(d.player)}>Undo</button>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      <div className="badge" style={{ marginTop: 8 }}>
        Tip: Drag a player from Suggestions/Undrafted onto a team row. Use the Draft
        button to add to <strong>your</strong> team.
      </div>
    </div>
  );
}
