import React, { useEffect, useRef, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { AlertCircle, FileText, Loader2 } from 'lucide-react';
import { PROMPTS, promptById } from '../data/prompts';
import SAMPLES from '../data/samples.json';
import { ScoreResult } from '../components/Result';

// Backend base URL: set VITE_API_URL at build time (e.g. in Vercel project settings).
const API_URL = (import.meta.env.VITE_API_URL || 'https://aes-grader-api.fly.dev').replace(/\/$/, '');

export default function Grade() {
  const [params, setParams] = useSearchParams();
  const [setId, setSetId] = useState(() => promptById(params.get('prompt'))?.id ?? 1);
  const [essay, setEssay] = useState('');
  const [sampleId, setSampleId] = useState(null); // human score shown only for an unedited sample
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);
  const [elapsed, setElapsed] = useState(null);
  const resultRef = useRef(null);
  const prompt = promptById(setId);
  const words = essay.trim() ? essay.trim().split(/\s+/).length : 0;
  const sample = SAMPLES[String(setId)];
  const humanScore = sampleId === setId && essay === sample.essay ? sample.human_score : null;

  useEffect(() => { setParams({ prompt: String(setId) }, { replace: true }); }, [setId, setParams]);

  const choose = (id) => { setSetId(id); setResult(null); setError(''); };
  const loadSample = () => { setEssay(sample.essay); setSampleId(setId); setResult(null); };

  const submit = async (e) => {
    e.preventDefault();
    setLoading(true); setError(''); setResult(null);
    const started = performance.now();
    try {
      const res = await fetch(`${API_URL}/score`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ essay, essay_set: setId }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(res.status === 422 ? 'The essay needs at least 10 characters.' : body.detail || `Server error (${res.status})`);
      }
      setResult(await res.json());
      setElapsed((performance.now() - started) / 1000);
      setTimeout(() => resultRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 50);
    } catch (err) {
      setError(err.message === 'Failed to fetch' ? 'Could not reach the grading server. Try again in a moment.' : err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container-page py-10 sm:py-14">
      <header className="max-w-prose">
        <p className="eyebrow">Grade an essay</p>
        <h1 className="mt-2 text-4xl font-semibold sm:text-[44px] sm:leading-[1.1]">Pick a prompt. Write or paste an essay.</h1>
        <p className="mt-3 text-ink2">
          The grader was trained on these eight prompts only, so it scores your essay against human-graded essays written for
          the same prompt. Off-topic essays get unreliable scores.
        </p>
      </header>

      <div className="mt-10 grid gap-8 lg:grid-cols-[320px_1fr]">
        <aside>
          <p className="eyebrow mb-3">Prompt</p>
          <ul className="space-y-1.5" role="listbox" aria-label="Essay prompt">
            {PROMPTS.map((p) => (
              <li key={p.id}>
                <button role="option" aria-selected={p.id === setId} onClick={() => choose(p.id)}
                  className={`w-full rounded-lg border px-3.5 py-2.5 text-left transition-colors ${
                    p.id === setId ? 'border-accent bg-accent-soft' : 'border-transparent hover:border-rule hover:bg-surface'}`}>
                  <span className="flex items-baseline justify-between gap-2">
                    <span className="text-[15px] font-medium text-ink">{p.title}</span>
                    <span className="shrink-0 text-xs text-muted num">Set {p.id}</span>
                  </span>
                  <span className="mt-0.5 block text-xs text-muted">{p.kind} · grade {p.grade} · scored {p.scale[0]}–{p.scale[1]}</span>
                </button>
              </li>
            ))}
          </ul>
        </aside>

        <section className="min-w-0 space-y-6">
          <div className="card p-6">
            <div className="flex flex-wrap items-baseline justify-between gap-2">
              <h2 className="text-2xl font-semibold">{prompt.title}</h2>
              <span className="text-sm text-muted">{prompt.kind} · grade {prompt.grade} · {prompt.scaleNote}</span>
            </div>
            {prompt.source && (
              <p className="mt-3 text-sm text-ink2">
                <FileText className="mr-1.5 inline h-4 w-4 -translate-y-px text-muted" />
                Students first read {prompt.source}. The text isn’t reproduced here.
              </p>
            )}
            <p className="mt-3 leading-relaxed text-ink2">{prompt.prompt}</p>
          </div>

          <form onSubmit={submit} className="card p-6">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <label htmlFor="essay" className="font-medium">Your essay</label>
              <button type="button" onClick={loadSample} className="text-sm text-accent hover:underline">
                Use a real sample essay for this prompt
              </button>
            </div>
            <textarea id="essay" value={essay} onChange={(e) => setEssay(e.target.value)} required minLength={10}
              onKeyDown={(e) => { if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) { e.preventDefault(); e.currentTarget.form.requestSubmit(); } }}
              placeholder="Start writing, or load a sample…"
              className="mt-3 h-72 w-full resize-y rounded-lg border border-rule bg-paper p-4 text-[15px] leading-relaxed text-ink placeholder:text-muted focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent/25" />
            <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
              <span className="text-sm text-muted num">{words} words <span className="hidden sm:inline">· Ctrl + Enter to grade</span></span>
              <button type="submit" className="btn-primary" disabled={loading || essay.trim().length < 10}>
                {loading ? (<><Loader2 className="h-4 w-4 animate-spin" /> Grading…</>) : 'Grade essay'}
              </button>
            </div>
            {sampleId === setId && essay === sample.essay && (
              <p className="mt-3 text-xs text-muted">
                Sample: ASAP essay #{sample.essay_id} from the held-out test set (the model never trained on it). Human
                raters scored it <span className="num font-medium text-ink2">{sample.human_score}</span>. Names and places were anonymised
                by the dataset (e.g. @LOCATION1).
              </p>
            )}
          </form>

          {error && (
            <p className="flex items-center gap-2 rounded-lg bg-pen-soft px-4 py-3 text-sm text-pen" role="alert">
              <AlertCircle className="h-4 w-4 shrink-0" /> {error}
            </p>
          )}

          {result && (
            <div ref={resultRef} className="card scroll-mt-24 p-6">
              {elapsed != null && <p className="mb-4 text-right text-xs text-muted num">Graded in {elapsed.toFixed(2)} s</p>}
              <ScoreResult result={result} prompt={prompt} humanScore={humanScore} />
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
