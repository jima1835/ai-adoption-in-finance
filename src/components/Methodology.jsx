import { STAGES, STAGE_LABELS, STAGE_DEFS } from '../data.js'

// Prose page — allowed to breathe more than the dense grid.
export default function Methodology() {
  return (
    <article className="prose">
      <h2 className="prose-h1">Methodology</h2>
      <p className="prose-lede">
        A public, sourced classification of AI adoption across institutional
        investors — pensions, sovereign-wealth funds, and endowments — organized
        by the stage each has actually reached, not the stage it markets.
      </p>

      <section>
        <h3 className="prose-h2">What this is</h3>
        <p>
          Most coverage of “AI in finance” collapses intent and execution into a
          single headline. This dashboard separates them. Every institution is
          placed in one of four stages based strictly on{' '}
          <strong>public evidence</strong> — news, official disclosures, board
          materials, position papers — and each placement carries a written
          rationale and a dated timeline back to its sources.
        </p>
      </section>

      <section>
        <h3 className="prose-h2">How the classification is made</h3>
        <p>
          The method has two distinct halves, and the distinction is the whole
          point:
        </p>
        <ul className="prose-list">
          <li>
            <strong>Humans assign the stage.</strong> Every adoption-stage
            classification and every timeline is curated by a person, reading
            public sources and exercising judgment. Stages are not generated,
            scored, or assigned by a model.
          </li>
          <li>
            <strong>Automation keeps the signal fresh.</strong> A daily search
            surfaces and summarizes new public signals so each institution’s
            “latest signal” stays current. That feed is an input to human review
            — it never moves an institution between stages on its own.
          </li>
        </ul>
        <p className="prose-callout">
          To be precise: AI does not update the classification. It helps a human
          notice what changed; the human decides whether anything has actually
          moved.
        </p>
      </section>

      <section>
        <h3 className="prose-h2">The four stages</h3>
        <dl className="stage-defs">
          {STAGES.map((stage) => (
            <div key={stage} className="stage-def-row" data-stage={stage}>
              <dt>
                <span className="stage-swatch" data-stage={stage} />
                {STAGE_LABELS[stage]}
              </dt>
              <dd>{STAGE_DEFS[stage]}</dd>
            </div>
          ))}
        </dl>
        <p className="prose-note">
          <strong>Embedded is intentionally empty.</strong> It is a real bar, not
          a missing tier: no institution treats AI as autonomous core
          infrastructure across the business — even the most advanced keep a
          human in control of every decision. The day that changes, the column
          fills.
        </p>
      </section>

      <section>
        <h3 className="prose-h2">Sources &amp; limits</h3>
        <p>
          Classifications rest only on public sources. Where an institution’s own
          claims (e.g. realized benefits “in the billions”) cannot be
          independently verified, they are labeled as company claims. Absence of
          a public signal is not proof of inaction — it is simply the limit of
          what can be sourced.
        </p>
      </section>

      <section className="author-bio">
        <h3 className="prose-h2">About the author</h3>
        <p className="prose-placeholder">
          [PLACEHOLDER — name, role, and links go here.]
        </p>
      </section>
    </article>
  )
}
