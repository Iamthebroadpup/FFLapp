import React from "react";

const POS = ["ALL", "QB", "RB", "WR", "TE", "K", "DST"];

export default function PositionFilter({
  value,
  onChange,
  compact = true,
}: {
  value: string;            // "", "QB", "RB", ...
  onChange: (pos: string) => void;
  compact?: boolean;
}) {
  const isActive = (p: string) => (value ? value === p : p === "ALL");
  return (
    <div className={`pos-filter ${compact ? "compact" : ""}`}>
      {POS.map((p) => {
        const val = p === "ALL" ? "" : p;
        return (
          <button
            key={p}
            className={isActive(p) ? "active" : ""}
            onClick={() => onChange(val)}
            type="button"
          >
            {p}
          </button>
        );
      })}
    </div>
  );
}
