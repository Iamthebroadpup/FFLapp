import { useEffect, useMemo, useState } from "react";
import SettingsBar from "./components/SettingsBar";
import PlayerTable from "./components/PlayerTable";
import SuggestPanel from "./components/SuggestPanel";
import DraftRoom from "./components/DraftRoom";
import { initSeason, listPlayers, suggest } from "./lib/api";
import { LeagueConfig, PlayerScore, Suggestion } from "./types";
import "./styles.css";

const DEFAULT_CFG: LeagueConfig = {
  season_year: 2025,
  season_type: "REG",
  teams: 12,
  roster: { QB: 1, RB: 2, WR: 2, TE: 1, FLEX: 1, DST: 1, K: 1 },
  scoring: {
    pass_yd: 0.04,
    pass_td: 4,
    pass_int: -2,
    rush_yd: 0.1,
    rush_td: 6,
    rec: 0.5,
    rec_yd: 0.1,
    rec_td: 6,
    fum_lost: -2,
    two_pt: 2,
    k_fg: 3,
    k_xp: 1,
    dst_sack: 1,
    dst_int: 2,
    dst_fr: 2,
    dst_safety: 2,
    dst_td: 6,
    dst_ret_td: 6,
    dst_pa_0: 10,
    dst_pa_1_6: 7,
    dst_pa_7_13: 4,
    dst_pa_14_20: 1,
    dst_pa_21_27: 0,
    dst_pa_28_34: -1,
    dst_pa_35p: -4,
  },
};

const LS_PICKS = "dh_picks";
const LS_OTHERS = "dh_others";
const LS_TEAM_NAMES = "dh_team_names";

export default function App() {
  const [cfg, setCfg] = useState<LeagueConfig>(DEFAULT_CFG);
  const [players, setPlayers] = useState<PlayerScore[]>([]);
  const [filtered, setFiltered] = useState<PlayerScore[]>([]);
  const [loading, setLoading] = useState(false);
  const [query, setQuery] = useState("");
  const [pos, setPos] = useState<"ALL" | "QB" | "RB" | "WR" | "TE" | "K" | "DST">("ALL");

  // --- Robust localStorage hydration (sanitized) ---
  const [picks, setPicks] = useState<number[]>(() => {
    try {
      const raw = JSON.parse(localStorage.getItem(LS_PICKS) || "[]");
      return Array.isArray(raw) ? raw.map(Number).filter((n) => Number.isFinite(n)) : [];
    } catch {
      return [];
    }
  });

  const [others, setOthers] = useState<[number, number][]>(() => {
    try {
      const raw = JSON.parse(localStorage.getItem(LS_OTHERS) || "[]");
      if (!Array.isArray(raw)) return [];
      const out: [number, number][] = [];
      for (const item of raw as any[]) {
        if (Array.isArray(item) && item.length >= 2) {
          const pid = Number(item[0]);
          const teamIdx = Number(item[1]);
          if (Number.isFinite(pid) && Number.isFinite(teamIdx)) out.push([pid, teamIdx]);
        }
      }
      return out;
    } catch {
      return [];
    }
  });

  const [teamNames, setTeamNames] = useState<string[]>(() => {
    const saved = localStorage.getItem(LS_TEAM_NAMES);
    if (saved) {
      try {
        const arr = JSON.parse(saved);
        if (Array.isArray(arr)) return arr;
      } catch {}
    }
    return Array.from({ length: DEFAULT_CFG.teams }).map((_, i) => `Team ${i + 1}`);
  });

  const drafted = useMemo(() => new Set(picks), [picks]);
  const taken = useMemo(() => new Set(others.map((o) => o[0])), [others]);

  const [sugs, setSugs] = useState<Suggestion[]>([]);
  const [snake, setSnake] = useState(true);
  const [userTeam, setUserTeam] = useState<number>(1);
  const [currentPick, setCurrentPick] = useState<number>(1);
  const [initError, setInitError] = useState<string | null>(null);

  // persist to localStorage
  useEffect(() => {
    localStorage.setItem(LS_PICKS, JSON.stringify(picks));
  }, [picks]);
  useEffect(() => {
    localStorage.setItem(LS_OTHERS, JSON.stringify(others));
  }, [others]);
  useEffect(() => {
    localStorage.setItem(LS_TEAM_NAMES, JSON.stringify(teamNames));
  }, [teamNames]);

  // keep teamNames length in sync with cfg.teams
  useEffect(() => {
    setTeamNames((prev) => {
      const copy = prev.slice(0, cfg.teams);
      while (copy.length < cfg.teams) copy.push(`Team ${copy.length + 1}`);
      return copy;
    });
  }, [cfg.teams]);

  async function doInit(year: number, type: "REG" | "PRE" | "POST") {
    setLoading(true);
    try {
      setInitError(null);
      await initSeason(year, type);

      const params = new URLSearchParams({
        teams: String(cfg.teams),
        scoring_pass_yd: String(cfg.scoring.pass_yd),
        scoring_pass_td: String(cfg.scoring.pass_td),
        scoring_pass_int: String(cfg.scoring.pass_int),
        scoring_rush_yd: String(cfg.scoring.rush_yd),
        scoring_rush_td: String(cfg.scoring.rush_td),
        scoring_rec: String(cfg.scoring.rec),
        scoring_rec_yd: String(cfg.scoring.rec_yd),
        scoring_rec_td: String(cfg.scoring.rec_td),
        scoring_fum_lost: String(cfg.scoring.fum_lost),
        scoring_two_pt: String(cfg.scoring.two_pt),
        scoring_k_fg: String(cfg.scoring.k_fg),
        scoring_k_xp: String(cfg.scoring.k_xp),
        scoring_dst_sack: String(cfg.scoring.dst_sack),
        scoring_dst_int: String(cfg.scoring.dst_int),
        scoring_dst_fr: String(cfg.scoring.dst_fr),
        scoring_dst_safety: String(cfg.scoring.dst_safety),
        scoring_dst_td: String(cfg.scoring.dst_td),
        scoring_dst_ret_td: String(cfg.scoring.dst_ret_td),
        scoring_dst_pa_0: String(cfg.scoring.dst_pa_0),
        scoring_dst_pa_1_6: String(cfg.scoring.dst_pa_1_6),
        scoring_dst_pa_7_13: String(cfg.scoring.dst_pa_7_13),
        scoring_dst_pa_14_20: String(cfg.scoring.dst_pa_14_20),
        scoring_dst_pa_21_27: String(cfg.scoring.dst_pa_21_27),
        scoring_dst_pa_28_34: String(cfg.scoring.dst_pa_28_34),
        scoring_dst_pa_35p: String(cfg.scoring.dst_pa_35p),
        roster_qb: String(cfg.roster.QB ?? 0),
        roster_rb: String(cfg.roster.RB ?? 0),
        roster_wr: String(cfg.roster.WR ?? 0),
        roster_te: String(cfg.roster.TE ?? 0),
        roster_flex: String(cfg.roster.FLEX ?? 0),
        roster_dst: String(cfg.roster.DST ?? 0),
        roster_k: String(cfg.roster.K ?? 0),
      });

      const data = await listPlayers(params);
      setPlayers(data);
    } catch (e: any) {
      setInitError(e?.message || String(e));
    } finally {
      setLoading(false);
    }
  }

  // initial load once
  useEffect(() => {
    doInit(cfg.season_year, cfg.season_type);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // keep filtered list in sync
  useEffect(() => {
    const q = query.toLowerCase();
    let arr = players.filter(
      (p) => !drafted.has(p.player.player_id) && !taken.has(p.player.player_id)
    );
    if (pos !== "ALL")
      arr = arr.filter((r) => {
        const P = r.player.position;
        if (pos === "DST") return P === "DST" || P === "DEF";
        return P === pos;
      });
    if (q)
      arr = arr.filter(
        (r) =>
          r.player.name.toLowerCase().includes(q) ||
          (r.player.team || "").toLowerCase().includes(q)
      );
    setFiltered(arr.slice(0, 400));
  }, [players, query, pos, drafted, taken]);

  // --- Suggestions ---
  async function recomputeSuggestions() {
    const s = await suggest({
      drafted_ids: picks,
      other_drafted_ids: others.map((o) => o[0]),
      config: cfg,
      user_team_index: userTeam,
      current_pick_overall: currentPick,
      snake: snake,
    });
    setSugs(s);
  }

  // Auto-refresh suggestions when draft state / controls change (debounced a bit)
  useEffect(() => {
    const t = setTimeout(() => {
      if (players.length) {
        recomputeSuggestions().catch((e) => console.error(e));
      }
    }, 200);
    return () => clearTimeout(t);
  }, [picks, others, cfg, userTeam, currentPick, snake, players]);

  function handleDraft(id: number) {
    if (!drafted.has(id) && !taken.has(id)) {
      setPicks([...picks, id]);
      setCurrentPick((x) => x + 1);
    }
  }
  function handleAssign(id: number, team: number) {
    if (team > 0 && !drafted.has(id) && !taken.has(id)) {
      setOthers([...others, [id, team]]);
      setCurrentPick((x) => x + 1);
    }
  }
  function handleUndo() {
    if (picks.length) {
      setPicks((p) => p.slice(0, -1));
      setCurrentPick((x) => Math.max(1, x - 1));
    } else if (others.length) {
      setOthers((o) => o.slice(0, -1));
      setCurrentPick((x) => Math.max(1, x - 1));
    }
  }
  function handleClear() {
    if (confirm("Clear all picks?")) {
      setPicks([]);
      setOthers([]);
      setCurrentPick(1);
    }
  }

  return (
    <div className="max-w-[1600px] mx-auto p-4 space-y-4">
      {/* widen the page so the table fits */}
      <h1 className="text-2xl font-bold">Fantasy Draft Helper</h1>

      {initError && (
        <div className="p-3 rounded bg-red-100 text-red-800">Init failed: {initError}</div>
      )}

      <SettingsBar cfg={cfg} setCfg={setCfg} onInit={doInit} />

      <div className="flex items-center gap-3 text-sm">
        <label className="flex items-center gap-1">
          <input
            type="checkbox"
            checked={snake}
            onChange={(e) => setSnake(e.target.checked)}
          />{" "}
          Snake draft
        </label>
        <label className="flex items-center gap-1">
          Your team #
          <input
            type="number"
            min={1}
            max={cfg.teams}
            value={userTeam}
            onChange={(e) => setUserTeam(Number(e.target.value))}
            className="w-16 border rounded px-2 py-1"
          />
        </label>
        <label className="flex items-center gap-1">
          Current pick
          <input
            type="number"
            min={1}
            value={currentPick}
            onChange={(e) => setCurrentPick(Number(e.target.value))}
            className="w-20 border rounded px-2 py-1"
          />
        </label>
        <button
          className="px-3 py-1 rounded bg-black text-white"
          onClick={() => recomputeSuggestions().catch(console.error)}
        >
          Suggest
        </button>
      </div>

      {/* HORIZONTAL: Draft Room | Suggestions | Players */}
      <div className="grid grid-cols-1 lg:grid-cols-3 lg:[grid-template-columns:1.1fr_0.9fr_1.8fr] gap-4">
        {/* Left */}
        <div className="space-y-3 min-w-0">
          <DraftRoom
            teams={cfg.teams}
            teamNames={teamNames}
            setTeamNames={setTeamNames}
            picks={picks}
            others={others}
            all={players}
            onAssign={handleAssign}
            onUndo={handleUndo}
            onClear={handleClear}
          />
        </div>

        {/* Middle */}
        <div className="space-y-3 min-w-0">
          <SuggestPanel items={sugs} refresh={recomputeSuggestions} cfg={cfg} />
        </div>

        {/* Right: search + Player list (scrollable if wide) */}
        <div className="space-y-3 min-w-0">
          <div className="flex items-center gap-2">
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search players/team…"
              className="px-3 py-2 border rounded w-full bg-white"
            />
            <select
              value={pos}
              onChange={(e) => setPos(e.target.value as any)}
              className="px-2 py-2 border rounded bg-white"
            >
              <option value="ALL">All</option>
              <option value="QB">QB</option>
              <option value="RB">RB</option>
              <option value="WR">WR</option>
              <option value="TE">TE</option>
              <option value="K">K</option>
              <option value="DST">DST</option>
            </select>
          </div>

          {/* Make the table scroll horizontally if it exceeds the column */}
          <div className="bg-white rounded-2xl shadow p-3 overflow-x-auto">
            <div className="min-w-[900px]">
              <PlayerTable
                rows={filtered}
                onDraft={handleDraft}
                onAssign={handleAssign}
                drafted={drafted}
                taken={taken}
                teams={cfg.teams}
                teamNames={teamNames}
                loading={loading}
              />
            </div>
          </div>
        </div>
      </div>

      <footer className="text-xs text-gray-500">
        Data: SportsDataIO (requires API key). Rankings = transparent points + VORP. PPR default; includes K &amp; DST.
      </footer>
    </div>
  );
}
