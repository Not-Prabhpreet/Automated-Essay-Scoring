import React from 'react';

// Inline SVG diagrams. Colours come from the theme (Tailwind fill-/stroke- classes on CSS
// variables), so each diagram is drawn for light and dark mode, not inverted.

function Defs({ id }) {
  return (
    <defs>
      <marker id={id} viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
        <path d="M0 0L10 5L0 10z" className="fill-muted" />
      </marker>
    </defs>
  );
}

function Box({ x, y, w, h, title, sub, tone = 'plain', dashed }) {
  const fill = { plain: 'fill-surface', accent: 'fill-accent-soft', pen: 'fill-pen-soft', sunk: 'fill-sunk' }[tone];
  const stroke = { plain: 'stroke-rule', accent: 'stroke-accent', pen: 'stroke-pen', sunk: 'stroke-rule' }[tone];
  return (
    <g>
      <rect x={x} y={y} width={w} height={h} rx="10" className={`${fill} ${stroke}`} strokeWidth="1.5" strokeDasharray={dashed ? '5 4' : undefined} />
      <text x={x + w / 2} y={y + (sub ? h / 2 - 3 : h / 2 + 5)} textAnchor="middle" className="fill-ink text-[14px] font-semibold">{title}</text>
      {sub && <text x={x + w / 2} y={y + h / 2 + 15} textAnchor="middle" className="fill-muted text-[12px]">{sub}</text>}
    </g>
  );
}

const Arrow = ({ d, m, dashed, label, lx, ly }) => (
  <g>
    <path d={d} fill="none" className="stroke-muted" strokeWidth="1.5" markerEnd={`url(#${m})`} strokeDasharray={dashed ? '5 4' : undefined} />
    {label && <text x={lx} y={ly} textAnchor="middle" className="fill-muted text-[11.5px]">{label}</text>}
  </g>
);

function Frame({ children, caption, minW = 720, viewBox }) {
  return (
    <figure className="my-8">
      <div className="overflow-x-auto rounded-xl border border-rule bg-paper p-4 sm:p-6">
        <svg viewBox={viewBox} className="w-full font-sans" style={{ minWidth: minW }} role="img" aria-label={caption}>
          {children}
        </svg>
      </div>
      <figcaption className="mt-2 text-sm text-muted">{caption}</figcaption>
    </figure>
  );
}

export function PipelineDiagram() {
  const m = 'arrow-pipeline';
  return (
    <Frame viewBox="0 0 900 380" caption="What happens to one essay. Solid boxes run on the live server; Kev (dashed) runs offline in the evaluation.">
      <Defs id={m} />
      <Box x={10} y={150} w={150} h={60} title="Essay + prompt" sub="one of 8 ASAP sets" tone="sunk" />
      <Box x={215} y={60} w={200} h={60} title="bge-small embedding" sub="384 numbers per essay" />
      <Box x={215} y={190} w={200} h={60} title="Style features" sub="20: length, spelling, vocabulary" />
      <Box x={465} y={60} w={200} h={60} title="Ridge head" sub="one per prompt" tone="accent" />
      <Box x={465} y={190} w={200} h={60} title="Nearest training essays" sub="cosine similarity" />
      <Box x={465} y={305} w={200} h={60} title="Kev rubric model" sub="one question per trait" dashed />
      <Box x={715} y={20} w={175} h={48} title="Score" tone="accent" />
      <Box x={715} y={100} w={175} h={60} title="90% range" sub="score ± q · σ" tone="accent" />
      <Box x={715} y={190} w={175} h={48} title="Similar essays" />
      <Box x={715} y={275} w={175} h={60} title="needs_review" sub="wide range or Kev disagrees" tone="pen" />
      <Arrow m={m} d="M160 170 C185 170 190 90 213 90" />
      <Arrow m={m} d="M160 190 C185 190 190 220 213 220" />
      <Arrow m={m} d="M415 90 H463" />
      <Arrow m={m} d="M415 220 C440 220 440 100 463 100" />
      <Arrow m={m} d="M330 120 C330 160 540 150 560 188" />
      <Arrow m={m} d="M665 80 C690 80 690 44 713 44" />
      <Arrow m={m} d="M665 100 C690 100 690 125 713 125" />
      <Arrow m={m} d="M665 210 C690 210 690 140 713 140" label="σ from neighbours" lx={705} ly={183} />
      <Arrow m={m} d="M665 225 C690 225 690 214 713 214" />
      <Arrow m={m} d="M802 160 V273" />
      <Arrow m={m} d="M665 335 C690 335 690 310 713 310" dashed />
      <Arrow m={m} d="M85 210 V335 H463" dashed />
    </Frame>
  );
}

export function SplitDiagram({ splits }) {
  const order = [
    ['train', 'Train', 'fits the heads; the only essays in the similarity index', 'fill-accent'],
    ['val', 'Val', 'every choice: model type, settings, thresholds', 'fill-ochre'],
    ['calib', 'Calib', 'only the conformal ranges', 'fill-ink2'],
    ['test', 'Test', 'read once, for every number on this page', 'fill-pen'],
  ];
  const total = order.reduce((a, [k]) => a + splits[k], 0);
  let x = 0;
  const W = 860;
  return (
    <Frame viewBox="0 0 900 165" minW={640}
      caption={`All ${total.toLocaleString()} essays, split per prompt with a fixed seed (42). Each essay is in exactly one part.`}>
      {order.map(([k, label, use, cls], i) => {
        const w = (splits[k] / total) * W;
        const x0 = 20 + x;
        x += w;
        return (
          <g key={k}>
            <rect x={x0 + 1} y={20} width={Math.max(w - 2, 2)} height={46} rx="6" className={cls} />
            <text x={x0 + 10} y={49} className="fill-paper text-[14px] font-semibold">{label} {Math.round((splits[k] / total) * 100)}%</text>
            <text x={20 + (i * W) / 4} y={100} className="fill-ink text-[13.5px] font-semibold">{label} · {splits[k].toLocaleString()}</text>
            <foreignObject x={20 + (i * W) / 4} y={108} width={W / 4 - 16} height={70}>
              <div className="text-[12.5px] leading-snug text-muted">{use}</div>
            </foreignObject>
          </g>
        );
      })}
    </Frame>
  );
}

export function WindowDiagram() {
  const m = 'arrow-window';
  const tokens = Array.from({ length: 44 }, (_, i) => i);
  return (
    <Frame viewBox="0 0 900 250" minW={680}
      caption="Long essays don’t fit the model’s 512-token window, so they are cut into overlapping windows (510 tokens, step 384). Each window is embedded, the vectors are averaged (weighted by length) and normalised.">
      <Defs id={m} />
      <text x={20} y={22} className="fill-muted text-[12px]">essay tokens (set 8 essays average ~800)</text>
      {tokens.map((i) => <rect key={i} x={20 + i * 19.5} y={32} width={16} height={22} rx="3" className="fill-sunk stroke-rule" />)}
      {[[0, 26, 'window 1'], [19, 44, 'window 2']].map(([a, b, label], j) => (
        <g key={label}>
          <path d={`M${20 + a * 19.5} ${66 + j * 16} h${(b - a) * 19.5 - 3}`} className="stroke-accent" strokeWidth="3" strokeLinecap="round" />
          <text x={20 + a * 19.5} y={84 + j * 16 + (j ? 4 : 0)} className="fill-ink2 text-[12px]">{label}</text>
        </g>
      ))}
      <Arrow m={m} d="M280 112 V140" />
      <Arrow m={m} d="M640 112 V140" />
      {[[200, 'vector 1'], [560, 'vector 2']].map(([x, label]) => (
        <g key={label}>
          {Array.from({ length: 12 }, (_, i) => (
            <rect key={i} x={x + i * 13} y={146} width={11} height={22} rx="2" className="fill-accent"
              opacity={0.25 + ((i * 37 + x) % 70) / 100} />
          ))}
          <text x={x} y={186} className="fill-muted text-[12px]">{label} · 384 numbers</text>
        </g>
      ))}
      <Arrow m={m} d="M370 160 C430 160 430 215 455 215" />
      <Arrow m={m} d="M560 160 C505 160 505 215 478 215" />
      <Box x={385} y={200} w={160} h={40} title="average + normalise" tone="accent" />
    </Frame>
  );
}

export function ConformalDiagram() {
  // Schematic: sorted calibration errors (normalised), the 90% quantile q, and a new essay.
  const errs = Array.from({ length: 40 }, (_, i) => Math.pow((i + 1) / 41, 1.6) * 2.4);
  const q = errs[Math.ceil(41 * 0.9) - 1];
  const X = (v) => 40 + (v / 2.6) * 380;
  const m = 'arrow-conf';
  return (
    <Frame viewBox="0 0 900 230" minW={700}
      caption="Schematic. Left: errors on the calibration essays, each divided by that essay’s difficulty σ, sorted. q is the value 90% of them fall under. Right: a new essay gets the range score ± q·σ.">
      <Defs id={m} />
      <text x={40} y={24} className="fill-ink text-[13.5px] font-semibold">1 · Calibration essays (never used for training)</text>
      <line x1={40} x2={420} y1={150} y2={150} className="stroke-rule" strokeWidth="1.5" />
      {errs.map((e, i) => (
        <circle key={i} cx={X(e)} cy={150 - 14 - (i % 4) * 16} r="5.5" className={e <= q ? 'fill-accent' : 'fill-pen'} />
      ))}
      <line x1={X(q)} x2={X(q)} y1={58} y2={160} className="stroke-ink" strokeWidth="1.5" strokeDasharray="4 3" />
      <text x={X(q) + 6} y={70} className="fill-ink text-[12.5px] font-semibold">q (90%)</text>
      <text x={40} y={175} className="fill-muted text-[12px]">|human − predicted| ÷ σ, small → large</text>
      <text x={40} y={195} className="fill-muted text-[12px]">green: inside q · red: the 10% outside</text>

      <text x={500} y={24} className="fill-ink text-[13.5px] font-semibold">2 · A new essay</text>
      <line x1={500} x2={880} y1={120} y2={120} className="stroke-rule" strokeWidth="3" strokeLinecap="round" />
      <rect x={600} y={110} width={180} height={20} rx="10" className="fill-accent-soft stroke-accent" strokeWidth="1.5" />
      <circle cx={690} cy={120} r="9" className="fill-accent stroke-surface" strokeWidth="3" />
      <text x={690} y={96} textAnchor="middle" className="fill-ink text-[12.5px]">predicted score</text>
      <path d="M600 146 h180" className="stroke-muted" strokeWidth="1.2" markerEnd={`url(#${m})`} markerStart={`url(#${m})`} />
      <text x={690} y={166} textAnchor="middle" className="fill-ink2 text-[12.5px]">score ± q · σ(essay)</text>
      <text x={690} y={186} textAnchor="middle" className="fill-muted text-[12px]">σ = 0.1 × scale + spread of the 25 nearest training essays’ scores</text>
    </Frame>
  );
}

export function KevDiagram({ example }) {
  const traits = Object.entries(example.traits);
  const m = 'arrow-kev';
  return (
    <Frame viewBox="0 0 900 345" minW={720}
      caption={`Real Kev output for test essay #${example.essay_id} (set 7). Both human raters gave 2 on every trait. Kev’s most likely level is usually right here, but its probability is spread over all four levels: that spread is why its agreement with raters is low.`}>
      <Defs id={m} />
      <Box x={10} y={40} w={175} h={64} title="State: the essay" sub="read once, cached" tone="sunk" />
      <Box x={10} y={130} w={175} h={84} title="4 score questions" sub="rubric levels 0–3 as options" />
      <text x={97} y={200} textAnchor="middle" className="fill-muted text-[11.5px]">wording from the ASAP rubric</text>
      <Box x={230} y={70} w={190} h={110} title="Qwen3.5-0.8B" sub="+ LoRA adapter" tone="accent" />
      <text x={325} y={160} textAnchor="middle" className="fill-muted text-[11.5px]">pointer head scores</text>
      <text x={325} y={173} textAnchor="middle" className="fill-muted text-[11.5px]">each option, no generation</text>
      <Arrow m={m} d="M185 72 C205 72 205 110 228 110" />
      <Arrow m={m} d="M185 172 C205 172 205 140 228 140" />
      <Arrow m={m} d="M420 125 H458" />
      <text x={470} y={22} className="fill-ink text-[13.5px] font-semibold">Probability of each rubric level</text>
      {traits.map(([name, t], r) => {
        const y = 40 + r * 70;
        return (
          <g key={name}>
            <text x={470} y={y + 22} className="fill-ink2 text-[12.5px]">{name[0].toUpperCase() + name.slice(1)}</text>
            {Object.entries(t.probs).map(([lvl, p], i) => (
              <g key={lvl}>
                <rect x={650 + i * 56} y={y + 42 - p * 95} width={40} height={Math.max(p * 95, 1)} rx="3"
                  className={Number(lvl) === t.human[0] ? 'fill-accent' : 'fill-ochre'} opacity={Number(lvl) === t.human[0] ? 1 : 0.55} />
                <text x={670 + i * 56} y={y + 56} textAnchor="middle" className="fill-muted text-[11px]">{lvl}</text>
              </g>
            ))}
            <text x={470} y={y + 40} className="fill-muted text-[11.5px] num">E = {t.expected.toFixed(2)} · conf {t.confidence.toFixed(2)}</text>
          </g>
        );
      })}
      <text x={470} y={336} className="fill-muted text-[11.5px]">green bar = the level both human raters chose</text>
    </Frame>
  );
}
