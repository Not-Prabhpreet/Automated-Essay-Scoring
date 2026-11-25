import React, { useState } from 'react';

// Charts follow the dataviz method: thin marks, 2px gaps, recessive grid, a legend,
// selective direct labels, per-mark hover tooltips and a table view. The two series
// colours (chart-base / chart-new) passed the palette validator in light and dark.

function Legend({ items }) {
  return (
    <div className="flex flex-wrap gap-x-5 gap-y-1 text-sm text-ink2">
      {items.map(([label, cls]) => (
        <span key={label} className="inline-flex items-center gap-2">
          <span className={`h-3 w-3 rounded-[3px] ${cls}`} /> {label}
        </span>
      ))}
    </div>
  );
}

function TableToggle({ show, setShow }) {
  return (
    <button onClick={() => setShow(!show)} className="text-sm text-accent hover:underline" aria-expanded={show}>
      {show ? 'Hide table' : 'Show as table'}
    </button>
  );
}

/** Grouped bars: QWK per prompt set for the original model and the new grader. */
export function QwkChart({ qwk }) {
  const [hover, setHover] = useState(null);
  const [table, setTable] = useState(false);
  const groups = [...qwk.sets.map((s) => ({ key: s, label: `Set ${s}` })), { key: 'mean', label: 'Mean' }];
  const val = (series, key) => (key === 'mean' ? series.mean : series.perSet[key]);
  const W = 860, H = 300, L = 44, B = 36, T = 16;
  const plotW = W - L - 10, plotH = H - B - T;
  const gw = plotW / groups.length;
  const bw = Math.min(26, gw / 2 - 8);
  const y = (v) => T + plotH * (1 - v);
  const bars = [['baseline', 'fill-chart-base'], ['deployed', 'fill-chart-new']];

  return (
    <figure className="my-8">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
        <Legend items={[[qwk.baseline.label, 'bg-chart-base'], [qwk.deployed.label, 'bg-chart-new']]} />
        <TableToggle show={table} setShow={setTable} />
      </div>
      <div className="relative overflow-x-auto rounded-xl border border-rule bg-surface p-4">
        <svg viewBox={`0 0 ${W} ${H}`} className="w-full font-sans" style={{ minWidth: 600 }} role="img"
          aria-label="Bar chart of quadratic weighted kappa per prompt set for both models">
          {[0, 0.2, 0.4, 0.6, 0.8, 1].map((t) => (
            <g key={t}>
              <line x1={L} x2={W - 10} y1={y(t)} y2={y(t)} className="stroke-rule" strokeWidth="1" />
              <text x={L - 8} y={y(t) + 4} textAnchor="end" className="fill-muted text-[11.5px] num">{t.toFixed(1)}</text>
            </g>
          ))}
          {groups.map((g, gi) => {
            const cx = L + gi * gw + gw / 2;
            return (
              <g key={g.key} onMouseEnter={() => setHover(gi)} onMouseLeave={() => setHover(null)}>
                <rect x={cx - gw / 2} y={T} width={gw} height={plotH} className={hover === gi ? 'fill-sunk' : 'fill-transparent'} />
                {bars.map(([k, cls], bi) => {
                  const v = val(qwk[k], g.key);
                  const x = cx + (bi === 0 ? -bw - 1 : 1);
                  return (
                    <g key={k}>
                      <path d={`M${x} ${y(0)} V${y(v) + 4} q0 -4 4 -4 h${bw - 8} q4 0 4 4 V${y(0)} z`} className={cls} />
                      {g.key === 'mean' && (
                        <text x={x + bw / 2} y={y(v) - 6} textAnchor="middle" className="fill-ink text-[12px] font-semibold num">{v.toFixed(2)}</text>
                      )}
                    </g>
                  );
                })}
                <text x={cx} y={H - B + 20} textAnchor="middle" className={`text-[12.5px] ${g.key === 'mean' ? 'fill-ink font-semibold' : 'fill-ink2'}`}>{g.label}</text>
              </g>
            );
          })}
          <line x1={L} x2={W - 10} y1={y(0)} y2={y(0)} className="stroke-muted" strokeWidth="1" />
        </svg>
        {hover != null && (
          <div className="pointer-events-none absolute top-3 rounded-lg border border-rule bg-surface px-3 py-2 text-sm shadow-md"
            style={{ left: `clamp(8px, calc(${((L + hover * gw + gw / 2) / W) * 100}% - 90px), calc(100% - 200px))` }}>
            <p className="font-medium text-ink">{groups[hover].label}</p>
            {bars.map(([k, cls]) => (
              <p key={k} className="mt-0.5 flex items-center gap-2 text-ink2">
                <span className={`h-2.5 w-2.5 rounded-[2px] ${cls.replace('fill-', 'bg-')}`} />
                {qwk[k].label}: <span className="num font-medium text-ink">{val(qwk[k], groups[hover].key).toFixed(3)}</span>
              </p>
            ))}
          </div>
        )}
      </div>
      {table && (
        <div className="mt-3 overflow-x-auto">
          <table className="w-full text-sm num">
            <thead><tr className="border-b border-rule text-left text-muted"><th className="py-2 pr-4 font-medium">Set</th>
              <th className="py-2 pr-4 font-medium">{qwk.baseline.label}</th><th className="py-2 font-medium">{qwk.deployed.label}</th></tr></thead>
            <tbody>
              {groups.map((g) => (
                <tr key={g.key} className="border-b border-rule/60">
                  <td className="py-1.5 pr-4 text-ink2">{g.label}</td>
                  <td className="py-1.5 pr-4">{val(qwk.baseline, g.key).toFixed(3)}</td>
                  <td className="py-1.5">{val(qwk.deployed, g.key).toFixed(3)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <figcaption className="mt-2 text-sm text-muted">
        Quadratic weighted kappa (QWK) on the held-out test essays: 1 is perfect agreement with the human score, 0 is chance.
        Hover a prompt for exact values.
      </figcaption>
    </figure>
  );
}
