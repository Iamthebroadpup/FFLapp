import React, { useEffect, useMemo, useState } from "react";
import { Player, Suggestion, ScoringRules, LeagueContext } from "./types";
import {
  initSeason,
  listPlayers,
  getSuggestions,
  draftPlayer,
  getDrafted,
  setRules as saveRulesApi,
  setContext as saveContextApi,
  undraftPlayer,
} from "./api";
import DraftBoard from "./components/DraftBoard";
import SettingsDrawer from "./components/SettingsDrawer";
import PositionFilter from "./components/PositionFilter";

export default function App() {
  // ---- Top-level state ----
  const [season, setSeason] = useState("2025");
  const [initd, setInitd] = useState(false);

  const [players, setPlayers] = useState<Player[]>([]);
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [drafted, setDrafted] = useState<{ player: Player; teamName: string }[]>(
    []
  );

  // Search + per-panel position filters
  const [q, setQ] = useState("");
  const [posUnd, setPosUnd] = useState<string>(""); // UNDRAFTED filter (server-side)
  const [posSug, setPosSug] = useState<string>(""); // SUGGESTIONS filter (client-side)

  // League rules + drawer
  const [rules, setRules] = useState<ScoringRules>({
    league_size: 12,
    roster_qb: 1,
    roster_rb: 2,
    roster_wr: 2,
    roster_te: 1,
    roster_flex: 1,
    roster_dst: 1,
    roster_k: 1,
    bench: 5,
    pass_td: 4,
    pass_yd: 0.04,
    pass_int: -2,
    rush_td: 6,
    rush_yd: 0.1,
    rec_td: 6,
    rec_yd: 0.1,
    ppr: 0.5,
    te_premium: 0,
  });
  const [context, setContextState] = useState<LeagueContext>({
    snake: true,
    teams: 12,
    pick_slot: 1,
    round: 1,
    total_rounds: 16,
    kdst_gate_round: 12,
  });
  const [drawerOpen, setDrawerOpen] = useState(false);

  // Team names (first = YOU / "ME")
  const defaultTeams = useMemo(
    () =>
      Array.from({ length: context.teams }, (_, i) =>
        i === 0 ? "ME" : `Team ${i + 1}`
      ),
    [context.teams]
  );
  const [teamNames, setTeamNames] = useState<string[]>(defaultTeams);

  useEffect(() => {
    // When league size changes, preserve any edited names within the new size
    setTeamNames((prev) => {
      const next = [...defaultTeams];
      for (let i = 0; i < Math.min(prev.length, next.length); i++) next[i] = prev[i];
      return next;
    });
  }, [defaultTeams]);

  // ---- Data fetching ----
  async function refreshLists() {
    const [P, S, D] = await Promise.all([
      listPlayers(q || undefined, posUnd || undefined),
      getSuggestions(12),
      getDrafted(),
    ]);
    setPlayers(P);
    setSuggestions(S);
    setDrafted(D);
  }

  // First load: init season then fetch lists
  useEffect(() => {
    (async () => {
      await initSeason(season);
      setInitd(true);
      await refreshLists();
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Re-fetch UNDRAFTED list when search or UND position changes
  useEffect(() => {
    if (!initd) return;
    const id = setTimeout(() => {
      refreshLists();
    }, 200);
    return () => clearTimeout(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [q, posUnd]);

  // Client-side filtered suggestions by position
  const filteredSuggestions = useMemo(
    () =>
      posSug
        ? suggestions.filter((s) => s.player.position === posSug)
        : suggestions,
    [suggestions, posSug]
  );

  // ---- Actions ----
  const onDraft = async (p: Player, teamName: string) => {
    await draftPlayer(p.player_id, teamName);
    await refreshLists();
  };

  const onUndraft = async (p: Player) => {
    await undraftPlayer(p.player_id);
    await refreshLists();
  };

  const onSaveRules = async (r: ScoringRules) => {
    const saved = await saveRulesApi(r);
    setRules(saved);
    await refreshLists();
  };

  const onSaveContext = async (c: LeagueContext) => {
    const saved = await saveContextApi(c);
    setContextState(saved);
    await refreshLists();
  };

  const renameTeam = (idx: number, name: string) => {
    setTeamNames((prev) => prev.map((t, i) => (i === idx ? name || t : t)));
  };

  // ---- Render ----
  return (
    <div className="app">
      {/* Top bar */}
      <div className="panel topbar">
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <strong>Fantasy Draft Assistant</strong>
          <span className="badge">Season</span>
          <input
            value={season}
            onChange={(e) => setSeason(e.target.value)}
            style={{ width: 80 }}
          />
          <button
            className="primary"
            onClick={async () => {
              await initSeason(season);
              await refreshLists();
            }}
          >
            Re-Init
          </button>
          <button onClick={() => setDrawerOpen(true)}>League Settings</button>
        </div>
        <div style={{ marginLeft: "auto", display: "flex", gap: 8 }}>
          <input
            placeholder="Search players or teams..."
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
          {/* Removed old global pos <select>; we now have per-panel filters */}
        </div>
      </div>

      {/* Left: Suggestions with its own position filter */}
      <div className="panel left">
        <div className="panel-header">
          <h3>Suggestions</h3>
          <PositionFilter value={posSug} onChange={setPosSug} />
        </div>
        <div className="list">
          {filteredSuggestions.map((s) => (
            <div
              key={s.player.player_id}
              className="player-card"
              draggable
              onDragStart={(e) => {
                e.dataTransfer.setData(
                  "application/x-player-id",
                  String(s.player.player_id)
                );
                e.dataTransfer.setData("text/plain", s.player.name);
              }}
            >
              <div>
                <div style={{ fontWeight: 700 }}>{s.player.name}</div>
                <div className="badge">
                  {s.player.team} • {s.player.position} • Bye{" "}
                  {s.player.bye_week || "-"}
                </div>
                <div className="badge">
                  ADP {s.player.adp || "-"} • Proj{" "}
                  {s.player.projected_points?.toFixed(1) || "-"}
                </div>
                <div className="badge">
                  {s.reasons.slice(0, 2).join(" • ")}
                </div>
              </div>
              <div style={{ textAlign: "right" }}>{s.score.toFixed(1)}</div>
              <button onClick={() => onDraft(s.player, teamNames[0])}>
                Draft
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Main: Undrafted with its own position filter (server-side) */}
      <div className="panel main">
        <div className="panel-header">
          <h3>Undrafted</h3>
          <PositionFilter value={posUnd} onChange={setPosUnd} />
        </div>
        <div className="list">
          {players.map((p) => (
            <div
              key={p.player_id}
              className="player-card"
              draggable
              onDragStart={(e) => {
                e.dataTransfer.setData(
                  "application/x-player-id",
                  String(p.player_id)
                );
                e.dataTransfer.setData("text/plain", p.name);
              }}
            >
              <div>
                <div style={{ fontWeight: 700 }}>{p.name}</div>
                <div className="badge">
                  {p.team} • {p.position} • Bye {p.bye_week || "-"}
                </div>
                <div className="badge">
                  ADP {p.adp || "-"} • Proj{" "}
                  {p.projected_points?.toFixed(1) || "-"}
                </div>
              </div>
              <div style={{ textAlign: "right" }}>
                {(p.projected_points || 0).toFixed(1)}
              </div>
              <button onClick={() => onDraft(p, teamNames[0])}>Draft</button>
            </div>
          ))}
        </div>
      </div>

      {/* Right: Draft Board (vertical teams, horizontal chips) */}
      <div className="panel right">
        <DraftBoard
          drafted={drafted}
          teamNames={teamNames}
          onRenameTeam={renameTeam}
          onUndraft={onUndraft}
          onDrop={onDraft}
        />
      </div>

      {/* Slide-out League Settings */}
      <SettingsDrawer
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        rules={rules}
        context={context}
        onSaveRules={onSaveRules}
        onSaveContext={onSaveContext}
      />
    </div>
  );
}
