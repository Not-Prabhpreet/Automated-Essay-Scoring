import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, BookOpenCheck, Flag, Ruler, Scale } from 'lucide-react';
import R from '../data/results.json';
import EXAMPLE from '../data/example_response.json';
import { promptById } from '../data/prompts';
import { ScoreResult } from '../components/Result';

const fmt = (x, d = 2) => Number(x).toFixed(d);
const pctf = (x) => `${(x * 100).toFixed(1)}%`;

const STATS = [
  { value: fmt(R.qwk.deployed.mean, 3), label: 'Agreement with human raters', note: `Mean QWK over 8 prompts. The original model scored ${fmt(R.qwk.baseline.mean, 3)}.` },
  { value: pctf(R.conformal.coverage), label: 'True scores inside the 90% range', note: `On ${R.dataset.splits.test.toLocaleString()} held-out test essays.` },
  { value: R.dataset.essays.toLocaleString(), label: 'Human-scored essays', note: 'From the ASAP dataset, grades 7 to 10.' },
  { value: '~0.1 s', label: 'Per essay', note: 'Typical response from the live server, network included.' },
];

const FEATURES = [
  { icon: Scale, title: 'A score on the real rubric scale', text: 'Each prompt keeps its own scale (1–6, 0–24, 0–60…) and its own model, trained on essays for that prompt.' },
  { icon: Ruler, title: 'A range, not just a number', text: 'Conformal prediction turns past errors into a range that contains the human score about 90% of the time.' },
  { icon: BookOpenCheck, title: 'Evidence you can check', text: 'The three most similar essays that humans graded, with their scores, so you can see what the model is comparing to.' },
  { icon: Flag, title: 'A flag when it’s unsure', text: 'Essays whose range is unusually wide for their prompt are marked for a teacher to read instead of trusting the number.' },
];

const LIMITS = [
  'It only knows the eight ASAP prompts. An essay on any other topic gets an unreliable score.',
  'Scores reflect how 2012 raters graded students in grades 7–10. It isn’t a judge of writing in general.',
  'The review flag catches about a third of large errors while flagging a fifth of essays, so an unflagged score can still be wrong.',
  'For practice and research, not for grades that matter to a student.',
];

export default function Home() {
  const prompt = promptById(EXAMPLE.essay_set);
  return (
    <>
      <section className="container-page grid items-center gap-12 pb-16 pt-14 sm:pt-20 lg:grid-cols-[1.05fr_1fr]">
        <div>
          <p className="eyebrow">Automated essay scoring</p>
          <h1 className="mt-3 text-[42px] font-semibold leading-[1.05] sm:text-[56px]">
            A grade, a range, and the reasons to trust it.
          </h1>
          <p className="mt-5 max-w-[52ch] text-lg leading-relaxed text-ink2">
            Score a student essay on one of eight real exam prompts. You get the score on the rubric’s own scale, a range that
            holds the human score 90% of the time, the closest essays human raters already graded, and a flag when a teacher
            should take a look.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link to="/grade" className="btn-primary">Grade an essay <ArrowRight className="h-4 w-4" /></Link>
            <Link to="/how-it-works" className="btn-secondary">How it works</Link>
          </div>
        </div>

        <figure className="card p-6 shadow-[0_1px_0_rgb(var(--rule)),0_20px_40px_-24px_rgb(0_0_0/0.25)]">
          <figcaption className="mb-5 flex items-baseline justify-between gap-3 border-b border-rule pb-4">
            <span className="font-serif text-lg font-semibold">{prompt.title}</span>
            <span className="text-xs text-muted">Real output · test essay #{EXAMPLE.essay_id}</span>
          </figcaption>
          <ScoreResult result={EXAMPLE} prompt={prompt} humanScore={EXAMPLE.human_score} compact />
        </figure>
      </section>

      <section className="border-y border-rule bg-surface">
        <dl className="container-page grid grid-cols-2 gap-x-6 gap-y-8 py-10 lg:grid-cols-4">
          {STATS.map((s) => (
            <div key={s.label}>
              <dt className="text-sm text-ink2">{s.label}</dt>
              <dd className="mt-1 font-serif text-4xl font-semibold num">{s.value}</dd>
              <dd className="mt-1 text-xs leading-snug text-muted">{s.note}</dd>
            </div>
          ))}
        </dl>
      </section>

      <section className="container-page py-20">
        <div className="max-w-prose">
          <p className="eyebrow">What you get back</p>
          <h2 className="mt-2 text-3xl font-semibold sm:text-4xl">One request, four answers.</h2>
        </div>
        <div className="mt-10 grid gap-x-10 gap-y-10 sm:grid-cols-2">
          {FEATURES.map(({ icon: Icon, title, text }) => (
            <div key={title} className="flex gap-4">
              <span className="grid h-10 w-10 shrink-0 place-items-center rounded-lg bg-accent-soft text-accent"><Icon className="h-5 w-5" /></span>
              <div>
                <h3 className="font-sans text-[17px] font-semibold">{title}</h3>
                <p className="mt-1.5 leading-relaxed text-ink2">{text}</p>
              </div>
            </div>
          ))}
        </div>
        <p className="mt-12">
          <Link to="/how-it-works" className="link inline-flex items-center gap-1.5">
            Read how the model, features and ranges work <ArrowRight className="h-4 w-4" />
          </Link>
        </p>
      </section>

      <section className="container-page">
        <div className="card grid gap-8 p-8 sm:p-10 lg:grid-cols-[1fr_1.4fr]">
          <div>
            <p className="eyebrow">Honest limits</p>
            <h2 className="mt-2 text-3xl font-semibold">What it can’t do</h2>
          </div>
          <ul className="space-y-3">
            {LIMITS.map((l) => (
              <li key={l} className="flex gap-3 text-ink2">
                <span className="mt-[11px] h-1.5 w-1.5 shrink-0 rounded-full bg-pen" />
                <span>{l}</span>
              </li>
            ))}
          </ul>
        </div>
      </section>
    </>
  );
}
