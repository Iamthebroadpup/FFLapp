// frontend/src/api.ts
import type { Player, Suggestion } from "./types";

export const API_BASE =
  (import.meta as any).env?.VITE_API_BASE || "http://127.0.0.1:8000";

// ---- Helpers ----
async function getJSON<T = any>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json() as Promise<T>;
}

async function postJSON<T = any>(url: string, body: any): Promise<T> {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json() as Promise<T>;
}

// ---- API ----
export async function initSeason(season?: number | string) {
  const q = season ? `?season=${encodeURIComponent(String(season))}` : "";
  return getJSON(`${API_BASE}/api/init${q}`);
}

export async function listPlayers(): Promise<Player[]> {
  return getJSON<Player[]>(`${API_BASE}/api/players`);
}

export async function draftPlayer(player_id: number, teamName: string) {
  // Backend expects { playerId, teamName }
  return postJSON(`${API_BASE}/api/draft`, { playerId: player_id, teamName });
}

export async function undraftPlayer(player_id: number) {
  // Backend expects { playerId }
  return postJSON(`${API_BASE}/api/undraft`, { playerId: player_id });
}

export async function getUndrafted(): Promise<Player[]> {
  return getJSON<Player[]>(`${API_BASE}/api/undrafted`);
}

export async function getDrafted(): Promise<{ player: Player; teamName: string }[]> {
  return getJSON<{ player: Player; teamName: string }[]>(`${API_BASE}/api/drafted`);
}



export async function getSuggestions(count = 12, pos?: string): Promise<Suggestion[]> {
  const params = new URLSearchParams();
  params.set("count", String(count));
  if (pos) params.set("pos", pos);
  try {
    const v2 = await getJSON<Suggestion[]>(`${API_BASE}/api/suggest_v2?${params.toString()}`);
    return Array.isArray(v2) ? v2 : [];
  } catch (err) {
    console.error("getSuggestions /api/suggest_v2 failed:", err);
    try {
      const v1 = await getJSON<Suggestion[]>(`${API_BASE}/api/suggest?${params.toString()}`);
      return Array.isArray(v1) ? v1 : [];
    } catch (err2) {
      console.error("legacy /api/suggest also failed:", err2);
      return [];
    }
  }
}

export async function setRules(rules: any) {
  return postJSON(`${API_BASE}/api/rules`, rules);
}
