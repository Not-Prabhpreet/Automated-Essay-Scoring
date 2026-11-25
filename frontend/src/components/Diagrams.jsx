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
    <Frame viewBox="0 0 900 300" caption="What happens to one essay. Everything runs on the server in about a tenth of a second.">
      <Defs id={m} />
      <Box x={10} y={120} w={150} h={60} title="Essay + prompt" sub="one of 8 ASAP sets" tone="sunk" />
      <Box x={215} y={40} w={200} h={60} title="TF-IDF" sub="word + character n-grams" />
      <Box x={215} y={200} w={200} h={60} title="Style features" sub="20: length, spelling, vocabulary" />
      <Box x={465} y={40} w={200} h={60} title="Ridge model" sub="one per prompt" tone="accent" />
      <Box x={465} y={200} w={200} h={60} title="Nearest training essays" sub="cosine similarity of word TF-IDF" />
      <Box x={715} y={10} w={175} h={48} title="Score" tone="accent" />
      <Box x={715} y={90} w={175} h={60} title="90% range" sub="score ± q · σ" tone="accent" />
      <Box x={715} y={180} w={175} h={48} title="Similar essays" />
      <Box x={715} y={240} w={175} h={56} title="needs_review" sub="range unusually wide" tone="pen" />
      <Arrow m={m} d="M160 140 C185 140 190 70 213 70" />
      <Arrow m={m} d="M160 160 C185 160 190 230 213 230" />
      <Arrow m={m} d="M415 70 H463" />
      <Arrow m={m} d="M415 230 C440 230 440 85 463 85" />
      <Arrow m={m} d="M330 100 C330 150 545 150 560 198" />
      <Arrow m={m} d="M665 60 C690 60 690 34 713 34" />
      <Arrow m={m} d="M665 80 C690 80 690 115 713 115" />
      <Arrow m={m} d="M665 215 C690 215 690 135 713 135" label="σ from neighbours" lx={700} ly={172} />
      <Arrow m={m} d="M665 235 C690 235 690 204 713 204" />
      <Arrow m={m} d="M890 150 C900 190 900 230 892 262" />
    </Frame>
  );
}

export function FeaturesDiagram({ example }) {
  const m = 'arrow-features';
  const maxW = Math.max(...example.words.map(([, w]) => w));
  const Bar = ({ x, y, label, w }) => (
    <g>
      <text x={x} y={y + 12} className="fill-ink2 text-[12.5px]">{label}</text>
      <rect x={x + 100} y={y + 2} width={Math.max((w / maxW) * 120, 3)} height={12} rx="3" className="fill-accent" />
      <text x={x + 106 + (w / maxW) * 120} y={y + 12} className="fill-muted text-[11px] num">{w.toFixed(2)}</text>
    </g>
  );
  const st = example.style;
  return (
    <Frame viewBox="0 0 900 250" minW={720}
      caption={`Real weights for sample essay #${example.essay_id} (set 7, the patience prompt). Highest-weighted word n-grams, highest letter-only character n-grams (“paite”, “aiten” come from the misspelling “paitent”), and three of the 20 style features. ASAP replaced names and places with placeholders such as @LOCATION3, so those become terms too. “the” gets only ${example.the.toFixed(2)}: every essay uses it.`}>
      <Defs id={m} />
      <Box x={10} y={100} w={150} h={60} title="One essay" sub="the student’s text" tone="sunk" />
      <text x={200} y={20} className="fill-ink text-[13.5px] font-semibold">Word n-grams (TF-IDF)</text>
      {example.words.map(([l, w], i) => <Bar key={l} x={200} y={30 + i * 22} label={l} w={w} />)}
      <text x={480} y={20} className="fill-ink text-[13.5px] font-semibold">Character n-grams (TF-IDF)</text>
      {example.chars.map(([l, w], i) => <Bar key={l + i} x={480} y={30 + i * 22} label={`“${l.trim()}”`} w={w} />)}
      <text x={200} y={176} className="fill-ink text-[13.5px] font-semibold">Style features</text>
      <text x={200} y={198} className="fill-ink2 text-[12.5px]">words (stop words removed): <tspan className="fill-ink font-semibold num">{st.word_count}</tspan></text>
      <text x={200} y={216} className="fill-ink2 text-[12.5px]">likely misspellings (in those words): <tspan className="fill-ink font-semibold num">{st.spelling_errors}</tspan></text>
      <text x={200} y={234} className="fill-ink2 text-[12.5px]">unique-word ratio: <tspan className="fill-ink font-semibold num">{st.unique_words_ratio}</tspan></text>
      <Arrow m={m} d="M160 120 C180 120 180 60 196 60" />
      <Arrow m={m} d="M160 140 C180 140 180 196 196 196" />
      <Box x={745} y={100} w={145} h={60} title="Ridge model" sub="weighted sum → score" tone="accent" />
      <Arrow m={m} d="M720 80 C735 80 735 115 743 115" />
      <Arrow m={m} d="M560 208 C700 208 715 150 743 145" />
      <text x={480} y={234} className="fill-muted text-[12px] num">{`${example.columns.toLocaleString()} columns for this prompt; ${example.nonzero.toLocaleString()} non-zero here`}</text>
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
