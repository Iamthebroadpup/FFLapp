import React, { useEffect, useMemo, useState } from "react";
import { Player, Suggestion, ScoringRules } from "./types";
import {
  initSeason,
  listPlayers,
  getSuggestions,
  draftPlayer,
  getDrafted,
  setRules as saveRulesApi,
  undraftPlayer,
} from "./api";
import DraftBoard from "./components/DraftBoard";
import SettingsDrawer from "./components/SettingsDrawer";
import PositionFilter from "./components/PositionFilter";

function fmt(v: any, digits = 1) {
  if (typeof v === 'number' && Number.isFinite(v)) return v.toFixed(digits);
  const n = Number(v);
  return Number.isFinite(n) ? n.toFixed(digits) : '-';
}

export default function App() {
  // ---- Top bar / session ----
  const [season, setSeason] = useState("2025");
  const [initd, setInitd] = useState(false);

  // ---- Data ----
  const [players, setPlayers] = useState<Player[]>([]);
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [drafted, setDrafted] = useState<{ player: Player; teamName: string }[]>([]);

  // ---- Filters ----
  const [q, setQ] = useState("");
  const [posUnd, setPosUnd] = useState<string>(""); // UNDRAFTED filter (client-side)
  const [posSug, setPosSug] = useState<string>(""); // SUGGESTIONS filter (client-side)

  // ---- League rules + drawer ----
  const [drawerOpen, setDrawerOpen] = useState(false);
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

  // ---- Team names (index 0 is ME) ----
  const defaultTeams = useMemo(
    () => Array.from({ length: rules.league_size }, (_, i) => (i === 0 ? "ME" : `Team ${i + 1}`)),
    [rules.league_size]
  );
  const [teamNames, setTeamNames] = useState<string[]>(defaultTeams);

  useEffect(() => {
    // Keep custom-edited names where possible when league size changes
    setTeamNames(prev => {
      const next = [...defaultTeams];
      for (let i = 0; i < Math.min(prev.length, next.length); i++) {
        if (i === 0 && prev[i] !== "ME") next[i] = prev[i];
        if (i > 0) next[i] = prev[i];
      }
      return next;
    });
  }, [defaultTeams]);

  // ---- Fetchers ----
  async function refreshLists() {
    const [P, S, D] = await Promise.all([
      listPlayers(),
      getSuggestions(12, posSug || undefined),
      getDrafted(),
    ]);
    setPlayers(P);
    setSuggestions(S);
    setDrafted(D);
  }

  // Initial load
  useEffect(() => {
    (async () => {
      await initSeason(season);
      setInitd(true);
      await refreshLists();
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Re-fetch when search or UND position changes
  useEffect(() => {
    if (!initd) return;
    const id = setTimeout(() => { refreshLists(); }, 150);
    return () => clearTimeout(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [q, posUnd]);

  // ---- Derived lists ----
  const playersFiltered = useMemo(() => {
    const ql = q.trim().toLowerCase();
    return players
      .filter(p => !posUnd || (p.position || "").toUpperCase() === posUnd.toUpperCase())
      .filter(p => {
        if (!ql) return true;
        return (
          p.name.toLowerCase().includes(ql) ||
          (p.team ? p.team.toLowerCase().includes(ql) : false)
        );
      });
  }, [players, q, posUnd]);

  const filteredSuggestions = useMemo(() => {
    return posSug
      ? suggestions.filter(s => (s.player.position || "").toUpperCase() === posSug.toUpperCase())
      : suggestions;
  }, [suggestions, posSug]);

  // ---- Actions ----
  const onSaveRules = async (r: ScoringRules) => {
    setRules(r);
    await saveRulesApi(r);
    // Recompute suggestions after rule change
    await refreshLists();
  };

  const onDraft = async (p: Player, teamName: string) => {
    await draftPlayer(p.player_id, teamName);
    await refreshLists();
  };

  const onUndraft = async (p: Player) => {
    await undraftPlayer(p.player_id);
    await refreshLists();
  };

  const onDrop = (p: Player, teamName: string) => {
    onDraft(p, teamName);
  };

  const renameTeam = (index: number, name: string) => {
    setTeamNames(prev => prev.map((t, i) => (i === index ? (name || t) : t)));
  };

  // ---- Render ----
  return (
    <div className="app">
      {/* Top bar */}
      <div className="panel topbar">
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <strong>Fantasy Draft Assistant</strong>
          <span className="badge">Season</span>
          <input value={season} onChange={e => setSeason(e.target.value)} style={{ width: 80 }} />
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
          <div className="pos-picker">
            <span className="badge">Suggestions</span>
            <PositionFilter value={posSug} onChange={setPosSug} />
          </div>
          <div className="pos-picker">
            <span className="badge">Undrafted</span>
            <PositionFilter value={posUnd} onChange={setPosUnd} />
          </div>
        </div>
      </div>

      {/* Left: Suggestions */}
      <div className="panel left">
        <h3>Suggestions</h3>
        <div className="list">
          {filteredSuggestions.map((s) => (
            <div
              key={s.player.player_id}
              className="player-card"
              draggable
              onDragStart={(e) => {
                e.dataTransfer.setData("application/x-player-id", String(s.player.player_id));
                e.dataTransfer.setData("text/plain", s.player.name);
              }}
            >
              <div>
                <div style={{ fontWeight: 700 }}>{s.player.name}</div>
                <div className="badge">
                  {s.player.team} • {s.player.position} • Bye {s.player.bye_week ?? "-"}
                </div>
                <div className="badge">
                  ADP {fmt(s.player.adp)} • Proj {fmt(s.player.projected_points)}
                </div>
                {Array.isArray((s as any).reasons) && (s as any).reasons.length > 0 ? (
                  <div className="badge">{(s as any).reasons.slice(0, 2).join(" • ")}</div>
                ) : null}
              </div>
              <div style={{ textAlign: "right" }}>{s.score.toFixed(1)}</div>
              <button onClick={() => onDraft(s.player, teamNames[0])}>Draft</button>
            </div>
          ))}
        </div>
      </div>

      {/* Middle: Undrafted */}
      <div className="panel middle">
        <h3>Undrafted</h3>
        <div className="list">
          {playersFiltered.map((p) => (
            <div
              key={p.player_id}
              className="player-card"
              draggable
              onDragStart={(e) => {
                e.dataTransfer.setData("application/x-player-id", String(p.player_id));
                e.dataTransfer.setData("text/plain", p.name);
              }}
            >
              <div>
                <div style={{ fontWeight: 700 }}>{p.name}</div>
                <div className="badge">
                  {p.team} • {p.position} • Bye {p.bye_week ?? "-"}
                </div>
                <div className="badge">
                  ADP {fmt(p.adp)} • Proj {fmt(p.projected_points)}
                </div>
              </div>
              <div style={{ textAlign: "right" }}>{fmt(p.projected_points)}</div>
              <button onClick={() => onDraft(p, teamNames[0])}>Draft</button>
            </div>
          ))}
        </div>
      </div>

      {/* Right: Draft Board */}
      <div className="panel right">
        <DraftBoard
          drafted={drafted}
          teamNames={teamNames}
          onRenameTeam={renameTeam}
          onUndraft={onUndraft}
          onDrop={onDrop}
        />
      </div>

      {/* Slide-out League Settings */}
      <SettingsDrawer
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        rules={rules}
        onSave={onSaveRules}
      />
    </div>
  );
}
