// frontend/src/api.ts
import type { LeagueContext } from "./types";

export const API_BASE =
  (import.meta as any).env?.VITE_API_BASE || "http://127.0.0.1:8000";

export type Player = {
  player_id: number;
  name: string;
  position: string;
  team?: string | null;
  age?: number | null;
  bye_week?: number | null;
  adp?: number | null;
  projected_points?: number | null;
  depth_order?: number | null;
  committee_size?: number | null;
};

export type UISuggestion = {
  player: Player;
  score: number;
  reasons: string[];
};

async function getJSON(url: string) {
  const r = await fetch(url);
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function initSeason(season?: string) {
  const url = `${API_BASE}/api/init${season ? `?season=${encodeURIComponent(season)}` : ""}`;
  return getJSON(url);
}

export async function listPlayers(q?: string, pos?: string) {
  const qs = new URLSearchParams();
  if (q) qs.set("q", q);
  if (pos) qs.set("pos", pos);
  return getJSON(`${API_BASE}/api/players?${qs.toString()}`);
}

export async function draftPlayer(playerId: number, teamName: string) {
  return fetch(`${API_BASE}/api/draft`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ playerId, teamName })
  }).then(r => r.json());
}

export async function undraftPlayer(playerId: number) {
  return fetch(`${API_BASE}/api/undraft`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ playerId })
  }).then(r => r.json());
}

export async function getUndrafted() {
  return getJSON(`${API_BASE}/api/undrafted`);
}

export async function getDrafted() {
  return getJSON(`${API_BASE}/api/drafted`);
}

function coerceV2ToUI(s: any): UISuggestion {
  const reasons =
    s?.reasons ??
    Object.entries(s?.components || {})
      .sort((a: any, b: any) => Math.abs(b[1]) - Math.abs(a[1]))
      .slice(0, 3)
      .map(([k, v]: any) => `${k}: ${Number(v).toFixed(2)}`);

  return {
    player: s.player,
    score: Number(s.score ?? 0),
    reasons: Array.isArray(reasons) ? reasons : []
  };
}

function coerceV1ToUI(s: any): UISuggestion {
  return {
    player: s.player,
    score: Number(s.score ?? 0),
    reasons: Array.isArray(s.reasons) ? s.reasons : []
  };
}

export async function getSuggestions(count = 12): Promise<UISuggestion[]> {
  // Try v2 first, then fall back to v1; never crash if shapes differ.
  try {
    const v2 = await getJSON(`${API_BASE}/api/suggest_v2?count=${count}`);
    return Array.isArray(v2) ? v2.map(coerceV2ToUI) : [];
  } catch {
    const v1 = await getJSON(`${API_BASE}/api/suggest?count=${count}`);
    return Array.isArray(v1) ? v1.map(coerceV1ToUI) : [];
  }
}

export async function setRules(rules: any) {
  return fetch(`${API_BASE}/api/rules`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(rules)
  }).then(r => r.json());
}

export async function setContext(ctx: LeagueContext) {
  return fetch(`${API_BASE}/api/context`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(ctx)
  }).then(r => r.json());
}
