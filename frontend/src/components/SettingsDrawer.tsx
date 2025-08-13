import React, { useState, useEffect } from "react";
import { ScoringRules } from "../types";

export default function SettingsDrawer({
  open,
  onClose,
  rules,
  onSave,
}: {
  open: boolean;
  onClose: () => void;
  rules: ScoringRules;
  onSave: (r: ScoringRules) => void;
}) {
  const [form, setForm] = useState<ScoringRules>(rules);
  useEffect(() => setForm(rules), [rules]);

  // Safely read a number from a number input
  const nv = (e: React.ChangeEvent<HTMLInputElement>) => {
    const n = e.currentTarget.valueAsNumber;
    return Number.isNaN(n) ? 0 : n;
  };

  const set = <K extends keyof ScoringRules>(k: K, v: number) =>
    setForm((f) => ({ ...f, [k]: v }));

  return (
    <>
      <div className={`drawer ${open ? "open" : ""}`}>
        <div className="drawer-header">
          <h3>League Settings</h3>
          <button onClick={onClose}>Close</button>
        </div>

        <div className="drawer-content">
          <h4>Rosters</h4>
          <div className="drawer-grid3">
            <label>Teams
              <input type="number" value={form.league_size}
                onChange={(e) => set("league_size", nv(e))} />
            </label>
            <label>QB
              <input type="number" value={form.roster_qb}
                onChange={(e) => set("roster_qb", nv(e))} />
            </label>
            <label>RB
              <input type="number" value={form.roster_rb}
                onChange={(e) => set("roster_rb", nv(e))} />
            </label>
            <label>WR
              <input type="number" value={form.roster_wr}
                onChange={(e) => set("roster_wr", nv(e))} />
            </label>
            <label>TE
              <input type="number" value={form.roster_te}
                onChange={(e) => set("roster_te", nv(e))} />
            </label>
            <label>FLEX
              <input type="number" value={form.roster_flex}
                onChange={(e) => set("roster_flex", nv(e))} />
            </label>
            <label>DST
              <input type="number" value={form.roster_dst}
                onChange={(e) => set("roster_dst", nv(e))} />
            </label>
            <label>K
              <input type="number" value={form.roster_k}
                onChange={(e) => set("roster_k", nv(e))} />
            </label>
            <label>Bench
              <input type="number" value={form.bench}
                onChange={(e) => set("bench", nv(e))} />
            </label>
          </div>

          <h4>Scoring</h4>
          <div className="drawer-grid3">
            <label>Pass TD
              <input type="number" step="0.1" value={form.pass_td}
                onChange={(e) => set("pass_td", nv(e))} />
            </label>
            <label>Pass Yd
              <input type="number" step="0.01" value={form.pass_yd}
                onChange={(e) => set("pass_yd", nv(e))} />
            </label>
            <label>INT
              <input type="number" step="0.1" value={form.pass_int}
                onChange={(e) => set("pass_int", nv(e))} />
            </label>
            <label>Rush TD
              <input type="number" step="0.1" value={form.rush_td}
                onChange={(e) => set("rush_td", nv(e))} />
            </label>
            <label>Rush Yd
              <input type="number" step="0.01" value={form.rush_yd}
                onChange={(e) => set("rush_yd", nv(e))} />
            </label>
            <label>Rec TD
              <input type="number" step="0.1" value={form.rec_td}
                onChange={(e) => set("rec_td", nv(e))} />
            </label>
            <label>Rec Yd
              <input type="number" step="0.01" value={form.rec_yd}
                onChange={(e) => set("rec_yd", nv(e))} />
            </label>
            <label>PPR
              <input type="number" step="0.1" value={form.ppr}
                onChange={(e) => set("ppr", nv(e))} />
            </label>
            <label>TE Premium
              <input type="number" step="0.1" value={form.te_premium}
                onChange={(e) => set("te_premium", nv(e))} />
            </label>
          </div>

          <div className="drawer-actions">
            <button className="primary" onClick={() => { onSave(form); onClose(); }}>
              Save
            </button>
          </div>
        </div>
      </div>

      {open && <div className="drawer-overlay" onClick={onClose} />}
    </>
  );
}
