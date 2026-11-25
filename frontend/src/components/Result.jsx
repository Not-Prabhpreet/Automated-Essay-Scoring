import React, { useState } from 'react';
import { AlertTriangle, CheckCircle2, ChevronDown } from 'lucide-react';

const pct = (v, lo, hi) => ((v - lo) / (hi - lo)) * 100;

// ASAP essays are Windows-1252 text read as Latin-1: curly quotes and dashes arrive as
// C1 control characters. Map them back for display.
const CP1252 = { '': '‘', '': '’', '': '“', '': '”', '': '–', '': '—', '': '…' };
export const cleanText = (t) => String(t).replace(/[-]/g, (c) => CP1252[c] ?? '');

/** The score scale with the 90% range as a band and the prediction as a marker. */
export function RangeBar({ low, high, score, scale, human }) {
  const [lo, hi] = scale;
  const ticks = hi - lo <= 12 ? Array.from({ length: hi - lo + 1 }, (_, i) => lo + i)
    : Array.from({ length: 7 }, (_, i) => Math.round(lo + (i * (hi - lo)) / 6));
  return (
    <div className="w-full" role="img"
      aria-label={`Predicted ${score} on a ${lo} to ${hi} scale; 90% range ${low} to ${high}${human != null ? `; human score ${human}` : ''}.`}>
      <div className="relative h-10">
        <div className="absolute inset-x-0 top-1/2 h-[3px] -translate-y-1/2 rounded-full bg-rule" />
        <div className="absolute top-1/2 h-3 -translate-y-1/2 rounded-full bg-accent/25 ring-1 ring-accent/50"
          style={{ left: `${pct(low, lo, hi)}%`, width: `max(${pct(high, lo, hi) - pct(low, lo, hi)}%, 12px)`,
                   transform: `translate(${low === high ? '-6px' : '0'}, -50%)` }} />
        {human != null && (
          <div className="absolute top-0 h-full w-[2px] -translate-x-1/2 bg-ochre" style={{ left: `${pct(human, lo, hi)}%` }}
            title={`Human score ${human}`} />
        )}
        <div className="absolute top-1/2 h-5 w-5 -translate-x-1/2 -translate-y-1/2 rounded-full border-[3px] border-surface bg-accent shadow-sm"
          style={{ left: `${pct(score, lo, hi)}%` }} />
      </div>
      <div className="relative mt-1 h-5 text-xs text-muted num">
        {ticks.map((t) => (
          <span key={t} className="absolute -translate-x-1/2" style={{ left: `${pct(t, lo, hi)}%` }}>{t}</span>
        ))}
      </div>
    </div>
  );
}

export function ReviewBadge({ needsReview, reasons }) {
  if (needsReview == null) return null;
  if (!needsReview) {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full bg-accent-soft px-3 py-1 text-sm font-medium text-accent">
        <CheckCircle2 className="h-4 w-4" /> No review needed
      </span>
    );
  }
  const text = { wide_range: 'the score range is unusually wide' };
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full bg-pen-soft px-3 py-1 text-sm font-medium text-pen">
      <AlertTriangle className="h-4 w-4" /> Worth a teacher’s look: {reasons.map((r) => text[r] || r).join(' and ')}
    </span>
  );
}

const RANK = ['Closest match', '2nd closest', '3rd closest'];

function SimilarEssay({ n, i }) {
  const [open, setOpen] = useState(false);
  return (
    <li className="rounded-lg border border-rule bg-paper/60 p-4">
      <div className="flex items-baseline justify-between gap-2">
        <span className="whitespace-nowrap text-sm text-ink2">Human score <span className="num text-base font-semibold text-ink">{n.score}</span></span>
        <span className="whitespace-nowrap text-xs text-muted" title={`Cosine similarity of word TF-IDF vectors: ${n.similarity.toFixed(3)}`}>{RANK[i] ?? `#${i + 1}`}</span>
      </div>
      <p className={`mt-2 text-sm leading-relaxed text-ink2 ${open ? '' : 'line-clamp-3'}`}>{cleanText(n.excerpt)}</p>
      <button onClick={() => setOpen(!open)} className="mt-1 text-xs text-accent hover:underline" aria-expanded={open}
        aria-label={`${open ? 'Collapse' : 'Expand'} similar essay ${i + 1}`}>
        {open ? 'Show less' : 'Show more'}
      </button>
    </li>
  );
}

/** Full grading result returned by POST /score. */
export function ScoreResult({ result, prompt, humanScore, compact = false }) {
  const [lo, hi] = prompt.scale;
  const hasRange = result.range && result.raw_score != null;
  const feedback = Object.entries(result.feedback || {});
  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="eyebrow">Score</p>
          {hasRange ? (
            <p className="mt-1 font-serif text-5xl font-semibold num">
              {result.raw_score}<span className="text-2xl text-muted"> / {hi}</span>
            </p>
          ) : (
            <p className="mt-1 font-serif text-5xl font-semibold num">{result.score.toFixed(1)}<span className="text-2xl text-muted"> / 10</span></p>
          )}
          {hasRange && (
            <p className="mt-1 text-sm text-muted">
              90% range <span className="num font-medium text-ink2">{result.range.low}–{result.range.high}</span>
              {' · '}{result.score.toFixed(1)} on a 0–10 scale
            </p>
          )}
        </div>
        <ReviewBadge needsReview={result.needs_review} reasons={result.review_reasons || []} />
      </div>

      {hasRange && (
        <div>
          <RangeBar low={result.range.low} high={result.range.high} score={result.raw_score} scale={[lo, hi]} human={humanScore} />
          <div className="mt-2 flex flex-wrap gap-x-5 gap-y-1 text-xs text-muted">
            <span className="inline-flex items-center gap-1.5"><span className="h-2.5 w-2.5 rounded-full bg-accent" /> Predicted score</span>
            <span className="inline-flex items-center gap-1.5"><span className="h-2.5 w-5 rounded-full bg-accent/25 ring-1 ring-accent/50" /> 90% range</span>
            {humanScore != null && <span className="inline-flex items-center gap-1.5"><span className="h-3 w-[2px] bg-ochre" /> Human score ({humanScore})</span>}
          </div>
        </div>
      )}

      {!compact && feedback.length > 0 && (
        <section>
          <h3 className="text-lg font-semibold">Writing feedback</h3>
          <ul className="mt-3 space-y-2">
            {feedback.flatMap(([cat, points]) => points.map((p, i) => (
              <li key={`${cat}-${i}`} className="flex gap-3 text-[15px] text-ink2">
                <span className="mt-[3px] shrink-0 rounded bg-sunk px-1.5 py-0.5 text-[11px] font-semibold uppercase tracking-wide text-muted">{cat}</span>
                <span>{p}</span>
              </li>
            )))}
          </ul>
          <p className="mt-2 text-xs text-muted">Rule-based hints from text statistics (sentence length, spelling, transitions). They don’t affect the score.</p>
        </section>
      )}

      {result.similar_essays?.length > 0 && (
        <section>
          <h3 className="text-lg font-semibold">{compact ? 'Closest human-graded essays' : 'Evidence: the closest human-graded essays'}</h3>
          {!compact && <p className="mt-1 text-sm text-muted">Training essays for the same prompt that share the most distinctive words and phrases with this one, and the score human raters gave them.</p>}
          <ol className={`mt-3 grid gap-3 ${compact ? '' : 'md:grid-cols-3'}`}>
            {result.similar_essays.slice(0, compact ? 2 : 3).map((n, i) => <SimilarEssay key={n.essay_id} n={n} i={i} />)}
          </ol>
        </section>
      )}

    </div>
  );
}

export function Disclosure({ title, children }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="rounded-lg border border-rule">
      <button onClick={() => setOpen(!open)} aria-expanded={open}
        className="flex w-full items-center justify-between px-4 py-3 text-left text-sm font-medium text-ink">
        {title} <ChevronDown className={`h-4 w-4 text-muted transition-transform ${open ? 'rotate-180' : ''}`} />
      </button>
      {open && <div className="border-t border-rule px-4 py-3 text-sm text-ink2">{children}</div>}
    </div>
  );
}
