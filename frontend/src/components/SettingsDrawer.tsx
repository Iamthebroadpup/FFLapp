import React, { useState, useEffect } from "react";
import { ScoringRules, LeagueContext } from "../types";

export default function SettingsDrawer({
  open,
  onClose,
  rules,
  context,
  onSaveRules,
  onSaveContext,
}: {
  open: boolean;
  onClose: () => void;
  rules: ScoringRules;
  context: LeagueContext;
  onSaveRules: (r: ScoringRules) => void | Promise<void>;
  onSaveContext: (c: LeagueContext) => void | Promise<void>;
}) {
  const [formRules, setFormRules] = useState<ScoringRules>(rules);
  const [formContext, setFormContext] = useState<LeagueContext>(context);
  useEffect(() => setFormRules(rules), [rules]);
  useEffect(() => setFormContext(context), [context]);

  // Safely read a number from a number input
  const nv = (e: React.ChangeEvent<HTMLInputElement>) => {
    const n = e.currentTarget.valueAsNumber;
    return Number.isNaN(n) ? 0 : n;
  };

  const setRule = <K extends keyof ScoringRules>(k: K, v: number) =>
    setFormRules((f) => ({ ...f, [k]: v }));
  const setCtx = <K extends keyof LeagueContext>(
    k: K,
    v: LeagueContext[K]
  ) => setFormContext((f) => ({ ...f, [k]: v }));

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
              <input
                type="number"
                value={formRules.league_size}
                onChange={(e) => setRule("league_size", nv(e))}
              />
            </label>
            <label>QB
              <input
                type="number"
                value={formRules.roster_qb}
                onChange={(e) => setRule("roster_qb", nv(e))}
              />
            </label>
            <label>RB
              <input
                type="number"
                value={formRules.roster_rb}
                onChange={(e) => setRule("roster_rb", nv(e))}
              />
            </label>
            <label>WR
              <input
                type="number"
                value={formRules.roster_wr}
                onChange={(e) => setRule("roster_wr", nv(e))}
              />
            </label>
            <label>TE
              <input
                type="number"
                value={formRules.roster_te}
                onChange={(e) => setRule("roster_te", nv(e))}
              />
            </label>
            <label>FLEX
              <input
                type="number"
                value={formRules.roster_flex}
                onChange={(e) => setRule("roster_flex", nv(e))}
              />
            </label>
            <label>DST
              <input
                type="number"
                value={formRules.roster_dst}
                onChange={(e) => setRule("roster_dst", nv(e))}
              />
            </label>
            <label>K
              <input
                type="number"
                value={formRules.roster_k}
                onChange={(e) => setRule("roster_k", nv(e))}
              />
            </label>
            <label>Bench
              <input
                type="number"
                value={formRules.bench}
                onChange={(e) => setRule("bench", nv(e))}
              />
            </label>
          </div>

          <h4>Scoring</h4>
          <div className="drawer-grid3">
            <label>Pass TD
              <input
                type="number"
                step="0.1"
                value={formRules.pass_td}
                onChange={(e) => setRule("pass_td", nv(e))}
              />
            </label>
            <label>Pass Yd
              <input
                type="number"
                step="0.01"
                value={formRules.pass_yd}
                onChange={(e) => setRule("pass_yd", nv(e))}
              />
            </label>
            <label>INT
              <input
                type="number"
                step="0.1"
                value={formRules.pass_int}
                onChange={(e) => setRule("pass_int", nv(e))}
              />
            </label>
            <label>Rush TD
              <input
                type="number"
                step="0.1"
                value={formRules.rush_td}
                onChange={(e) => setRule("rush_td", nv(e))}
              />
            </label>
            <label>Rush Yd
              <input
                type="number"
                step="0.01"
                value={formRules.rush_yd}
                onChange={(e) => setRule("rush_yd", nv(e))}
              />
            </label>
            <label>Rec TD
              <input
                type="number"
                step="0.1"
                value={formRules.rec_td}
                onChange={(e) => setRule("rec_td", nv(e))}
              />
            </label>
            <label>Rec Yd
              <input
                type="number"
                step="0.01"
                value={formRules.rec_yd}
                onChange={(e) => setRule("rec_yd", nv(e))}
              />
            </label>
            <label>PPR
              <input
                type="number"
                step="0.1"
                value={formRules.ppr}
                onChange={(e) => setRule("ppr", nv(e))}
              />
            </label>
            <label>TE Premium
              <input
                type="number"
                step="0.1"
                value={formRules.te_premium}
                onChange={(e) => setRule("te_premium", nv(e))}
              />
            </label>
          </div>

          <h4>Draft Context</h4>
          <div className="drawer-grid3">
            <label>Snake
              <input
                type="checkbox"
                checked={formContext.snake}
                onChange={(e) => setCtx("snake", e.currentTarget.checked)}
              />
            </label>
            <label>Teams
              <input
                type="number"
                value={formContext.teams}
                onChange={(e) => setCtx("teams", nv(e))}
              />
            </label>
            <label>Pick Slot
              <input
                type="number"
                value={formContext.pick_slot}
                onChange={(e) => setCtx("pick_slot", nv(e))}
              />
            </label>
            <label>Round
              <input
                type="number"
                value={formContext.round}
                onChange={(e) => setCtx("round", nv(e))}
              />
            </label>
            <label>Total Rounds
              <input
                type="number"
                value={formContext.total_rounds}
                onChange={(e) => setCtx("total_rounds", nv(e))}
              />
            </label>
            <label>K/DST Gate Round
              <input
                type="number"
                value={formContext.kdst_gate_round}
                onChange={(e) => setCtx("kdst_gate_round", nv(e))}
              />
            </label>
          </div>

          <div className="drawer-actions">
            <button
              className="primary"
              onClick={async () => {
                await onSaveRules(formRules);
                await onSaveContext(formContext);
                onClose();
              }}
            >
              Save
            </button>
          </div>
        </div>
      </div>

      {open && <div className="drawer-overlay" onClick={onClose} />}
    </>
  );
}
