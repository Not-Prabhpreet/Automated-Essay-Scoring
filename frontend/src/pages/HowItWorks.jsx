import React from 'react';
import { Link } from 'react-router-dom';
import R from '../data/results.json';
import FEATURES_EXAMPLE from '../data/features_example.json';
import { PROMPTS } from '../data/prompts';
import { QwkChart } from '../components/Charts';
import { ConformalDiagram, FeaturesDiagram, PipelineDiagram, SplitDiagram } from '../components/Diagrams';
import { REPO_URL } from '../components/Layout';

const p1 = (x) => `${(x * 100).toFixed(1)}%`;
const f3 = (x) => Number(x).toFixed(3);

const SECTIONS = [
  ['overview', 'Overview'], ['data', 'The data'], ['features', 'Features'], ['scoring', 'Scoring model'],
  ['results', 'Results'], ['ranges', 'Score ranges'], ['evidence', 'Similar essays'], ['review', 'Review flag'],
  ['engineering', 'Making it fast'], ['limits', 'Limits'],
];

function Section({ id, eyebrow, title, children }) {
  return (
    <section id={id} className="scroll-mt-24 border-t border-rule pt-12 first:border-t-0 first:pt-0">
      {eyebrow && <p className="eyebrow">{eyebrow}</p>}
      <h2 className="mt-2 text-3xl font-semibold">{title}</h2>
      <div className="prose-body mt-5 max-w-prose">{children}</div>
    </section>
  );
}

function Prose({ children }) {
  return <div className="prose-body max-w-prose">{children}</div>;
}

function Table({ head, rows, caption }) {
  return (
    <figure className="my-6 max-w-none">
      <div className="overflow-x-auto rounded-xl border border-rule bg-surface">
        <table className="w-full text-sm num">
          <thead><tr className="border-b border-rule bg-sunk/60 text-left text-muted">
            {head.map((h) => <th key={h} className="px-4 py-2.5 font-medium">{h}</th>)}
          </tr></thead>
          <tbody>
            {rows.map((r, i) => (
              <tr key={i} className="border-b border-rule/60 last:border-0">
                {r.map((c, j) => <td key={j} className={`px-4 py-2 ${j === 0 ? 'text-ink' : 'text-ink2'}`}>{c}</td>)}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {caption && <figcaption className="mt-2 text-sm text-muted">{caption}</figcaption>}
    </figure>
  );
}

export default function HowItWorks() {
  const ab = R.qwk.ablations;
  const rb = R.review.budgets;
  return (
    <div className="container-page py-10 sm:py-14">
      <header className="max-w-prose">
        <p className="eyebrow">How it works</p>
        <h1 className="mt-2 text-4xl font-semibold sm:text-[48px] sm:leading-[1.08]">The model, the data, and how far to trust them</h1>
        <p className="mt-4 text-lg text-ink2">
          Every number on this page comes from the evaluation scripts in the{' '}
          <a className="link" href={REPO_URL} target="_blank" rel="noreferrer">repository</a> and is measured on essays the
          model never saw.
        </p>
      </header>

      <div className="mt-12 grid gap-12 lg:grid-cols-[200px_1fr]">
        <nav className="hidden lg:block" aria-label="On this page">
          <ul className="sticky top-24 space-y-1 border-l border-rule text-sm">
            {SECTIONS.map(([id, label]) => (
              <li key={id}><a href={`#${id}`} className="-ml-px block border-l border-transparent py-1 pl-4 text-ink2 hover:border-accent hover:text-ink">{label}</a></li>
            ))}
          </ul>
        </nav>

        <div className="min-w-0 space-y-14">
          <Section id="overview" eyebrow="1" title="Overview">
            <p>
              The grader turns an essay into numbers in two ways. TF-IDF counts which words, word pairs and letter sequences
              the essay uses, weighted by how distinctive they are. Twenty style features measure things like length,
              spelling mistakes and vocabulary. A separate linear model for each prompt maps those numbers to a score on that
              prompt’s scale.
            </p>
            <p>
              Around that score sit three things a single number can’t tell you: how wide the plausible range is, which
              human-graded essays it resembles, and whether a teacher should check it. The whole thing is plain linear
              algebra, so it runs in about a tenth of a second on a small server.
            </p>
          </Section>
          <PipelineDiagram />

          <Section id="data" eyebrow="2" title="The data">
            <p>
              The <a className="link" href="https://www.kaggle.com/c/asap-aes" target="_blank" rel="noreferrer">Automated Student
              Assessment Prize</a> (ASAP) dataset has {R.dataset.essays.toLocaleString()} essays written by students in grades 7
              to 10 for eight prompts, each scored by trained human raters. Four prompts are argument or story essays; four ask
              students to respond to a short text they had just read. Each prompt has its own rubric and scale, from 0–3 up to 0–60.
            </p>
            <p>
              The essays are split once, per prompt, with a fixed random seed. The split is committed to the repository, so
              every model is compared on exactly the same test essays.
            </p>
          </Section>
          <SplitDiagram splits={R.dataset.splits} />
          <Table head={['Set', 'Prompt', 'Type', 'Grade', 'Score scale']}
            rows={PROMPTS.map((p) => [p.id, p.title, p.kind, p.grade, `${p.scale[0]}–${p.scale[1]}`])} />

          <Section id="features" eyebrow="3" title="Features: TF-IDF and style">
            <p>
              <strong className="text-ink">TF-IDF</strong> (term frequency × inverse document frequency) gives every term a weight for
              each essay. The weight is high when the term appears in this essay but is rare across the prompt’s training essays,
              and close to zero for words every essay uses. Two kinds of terms are counted:
            </p>
            <p>
              <em>Word n-grams</em>, single words and word pairs, capture what the essay talks about and how it phrases it.
              <em> Character n-grams</em>, runs of 2 to 5 letters inside words, capture spelling, word forms and vocabulary level,
              and they still match when a word is misspelled.
            </p>
            <p>
              <strong className="text-ink">Style features</strong> are the 20 measurements the original project used: word and
              sentence counts, likely spelling mistakes, vocabulary richness, transition words and similar. They are rescaled so
              no single one dominates.
            </p>
          </Section>
          <FeaturesDiagram example={FEATURES_EXAMPLE} />

          <Section id="scoring" eyebrow="4" title="Scoring model">
            <p>
              Each prompt gets its own model, trained only on that prompt’s training essays. It is a ridge regression: a weighted sum of
              all the TF-IDF and style columns, with a penalty that keeps weights small so it doesn’t memorise about a thousand
              training essays. The penalty strength is chosen per prompt on the validation essays. Scoring a new essay is one
              sparse dot product.
            </p>
          </Section>
          <Table head={['Variant', 'Mean QWK (test)']}
            caption="Mean QWK across the eight prompts on the held-out test essays. Each variant chose its settings on validation essays only."
            rows={Object.entries(ab).map(([k, val]) => { const n = k.replace('(baseline)', '').replace(', deployed', ' (deployed)').trim(); return [n[0].toUpperCase() + n.slice(1), f3(val)]; })} />
          <Prose>
            <p>
              Neither half is enough alone: style features reach {f3(ab['style features only (ridge)'])} and TF-IDF{' '}
              {f3(ab['TF-IDF only (ridge)'])}, but together they reach {f3(ab['TF-IDF + style (ridge), deployed'])}. TF-IDF catches content
              and phrasing; the style features catch length and surface quality.
            </p>
          </Prose>

          <Section id="results" eyebrow="5" title="Results per prompt">
            <p>
              Agreement is measured with quadratic weighted kappa (QWK), the ASAP competition metric. It is 1 for perfect
              agreement with the human score and 0 for chance, and it penalises a miss of two points four times as much as a
              miss of one.
            </p>
          </Section>
          <QwkChart qwk={R.qwk} />
          <Prose>
            <p>
              The new model is better on seven of eight prompts and about equal on set 1, where the original model had been
              partly trained on the test essays. The biggest gains are on the short reading responses (sets 3 and 4) and the
              narrative prompt (set 7), where the original model was weakest.
            </p>
          </Prose>

          <Section id="ranges" eyebrow="6" title="Score ranges (conformal prediction)">
            <p>
              A single predicted score hides how sure the model is. The grader also returns a range built with{' '}
              <em>split conformal prediction</em>, a method that makes few assumptions: if a new essay is like the essays
              set aside for calibration, its human score falls inside the range at least 90% of the time.
            </p>
            <p>
              It works by looking at the model’s errors on {Object.values(R.conformal.perSet).reduce((a, s) => a + s.nCalib, 0).toLocaleString()} calibration
              essays the model never trained on. Each error is divided by a difficulty estimate σ: how much the human scores of
              the essay’s {R.conformal.k} most similar training essays disagree with each other. q is the size of error that 90% of
              calibration essays stay under, and a new essay gets <code>score ± q·σ</code>. Essays that resemble essays humans
              scored very differently get wider ranges.
            </p>
          </Section>
          <ConformalDiagram />
          <Table head={['Set', 'Scale', 'Coverage (target 90%)', 'Average width', 'Calibration essays']}
            caption={`Test essays inside their range: ${p1(R.conformal.coverage)} overall, with ranges averaging ${p1(R.conformal.widthFrac)} of the score scale. The simpler fixed-width version covers ${p1(R.conformal.plain.test_coverage_overall)} at ${p1(R.conformal.plain.test_mean_width_frac_of_range)}, but gives every essay of a prompt the same width.`}
            rows={Object.entries(R.conformal.perSet).map(([s, c]) => [s, `${c.range[0]}–${c.range[1]}`, p1(c.coverage), `${c.width.toFixed(1)} points`, c.nCalib])} />

          <Section id="evidence" eyebrow="7" title="Similar essays as evidence">
            <p>
              For every essay the grader returns the three training essays for the same prompt whose word TF-IDF vectors are
              closest (cosine similarity), with the score humans gave them. Essays that share distinctive words and phrases
              tend to make similar points. If your essay scored 3 and its closest neighbours scored 2, 3 and 3, the score is
              easy to believe. If they scored 1, 4 and 2, be careful.
            </p>
            <p>
              The search only covers training essays, so a test essay can never retrieve itself or its own score. Tests in the
              repository check this, along with the rule that each essay sits in exactly one split.
            </p>
          </Section>

          <Section id="review" eyebrow="8" title="The review flag">
            <p>
              <code>needs_review</code> is set when an essay’s range is unusually wide compared with other essays for the same
              prompt. The cut-off is chosen on validation essays to catch as many large errors as possible while flagging about
              20% of essays. A large error is a miss of at least 2 points and at least a fifth of the scale.
            </p>
            <p>
              Large errors are rare: {R.review.largeErrors} of {R.dataset.splits.test.toLocaleString()} test essays
              ({p1(R.review.largeErrorRate)}). Flagging a fifth of essays catches about a third of them, so the flag helps, but a
              teacher shouldn’t treat unflagged scores as certain.
            </p>
          </Section>
          <Table head={['Flag budget', 'Essays flagged', 'Large errors caught']}
            caption="Test essays; each cut-off was chosen on validation. The live server uses the 20% budget."
            rows={Object.entries(rb).map(([b, v]) => [`${Math.round(Number(b) * 100)}%`, p1(v.flagged), p1(v.caught)])} />

          <Section id="engineering" eyebrow="9" title="Making it fast">
            <p>
              The live server returns a grade in about a tenth of a second, network included; grading itself takes a median of{' '}
              {Math.round(R.speed.inProcessMedianMs)} ms. It runs on a single shared CPU with 512 MB of memory. Four things keep it
              that way:
            </p>
          </Section>
          <Table head={['Technique', 'Effect']} rows={[
            ['TF-IDF and a linear model instead of a neural network', 'scoring a new essay is one sparse dot product; no GPU, no model download'],
            ['Spelling feature: dictionary lookup first; for unknown words, a precomputed index of one-letter deletions answers “is a dictionary word within two edits?”', 'same answers as TextBlob’s spell checker (tested), from ~2 s to milliseconds per essay'],
            ['The original project’s TensorFlow model is only imported if it is ever needed', '~350 MB of memory instead of ~850 MB'],
            ['Slim Docker image, one thread per CPU, a warm-up request at start-up', '147 MB image; the first visitor doesn’t wait for loading'],
          ]} />

          <Section id="limits" eyebrow="10" title="Limits">
            <p>
              The grader only knows these eight prompts and the way 2012 raters scored grade 7–10 students. Scores for essays on
              other topics are meaningless, and the reading-response prompts assume the student read a text the model never sees.
              TF-IDF rewards using the vocabulary that good essays for a prompt tend to use, so an essay could game it by
              stuffing in the right words. A mean QWK of 0.75 is strong agreement, but individual scores still miss. The range and
              the flag exist so you don’t have to take any one number on trust.
            </p>
            <p>
              <Link to="/grade" className="link">Try it on a real test essay</Link>, or read the{' '}
              <a className="link" href={REPO_URL} target="_blank" rel="noreferrer">code and evaluation scripts</a>.
            </p>
          </Section>
        </div>
      </div>
    </div>
  );
}
