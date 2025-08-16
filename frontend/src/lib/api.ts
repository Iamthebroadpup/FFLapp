import { PlayerScore, Suggestion, LeagueConfig } from "../types";

const BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

export async function initSeason(year: number, seasonType: 'REG'|'PRE'|'POST'='REG') {
  const r = await fetch(`${BASE}/api/init?season=${year}&season_type=${seasonType}`);
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function listPlayers(params: URLSearchParams) : Promise<PlayerScore[]> {
  const r = await fetch(`${BASE}/api/players?${params.toString()}`);
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function suggest(body: {
  drafted_ids: number[];
  other_drafted_ids: number[];
  config: LeagueConfig;
  user_team_index?: number;
  current_pick_overall?: number;
  snake?: boolean;
}): Promise<Suggestion[]> {
  const r = await fetch(`${BASE}/api/suggest`, {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify(body)
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}
