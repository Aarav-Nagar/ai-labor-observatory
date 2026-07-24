import { useEffect, useMemo, useState } from "react";
import type { Geography, ObservatorySummary } from "./types";

const money = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 0,
});
const integer = new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 });

function prettyLabel(value: string) {
  return value
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function Metric({
  eyebrow,
  value,
  detail,
}: {
  eyebrow: string;
  value: string;
  detail: string;
}) {
  return (
    <article className="metric-card">
      <span>{eyebrow}</span>
      <strong>{value}</strong>
      <p>{detail}</p>
    </article>
  );
}

function HorizontalBar({
  value,
  maximum,
  accent = false,
}: {
  value: number;
  maximum: number;
  accent?: boolean;
}) {
  const width = maximum === 0 ? 0 : Math.max(2, (value / maximum) * 100);
  return (
    <div className="bar-track" aria-label={`${value.toFixed(1)} out of ${maximum.toFixed(1)}`}>
      <div
        className={accent ? "bar-fill accent" : "bar-fill"}
        style={{ width: `${width}%` }}
      />
    </div>
  );
}

function App() {
  const [data, setData] = useState<ObservatorySummary | null>(null);
  const [error, setError] = useState("");
  const [selectedSoc, setSelectedSoc] = useState("");

  useEffect(() => {
    fetch(`${import.meta.env.BASE_URL}data/summary.json`)
      .then((response) => {
        if (!response.ok) throw new Error("The analytical snapshot could not be loaded.");
        return response.json();
      })
      .then((payload: ObservatorySummary) => {
        setData(payload);
        if (payload.geography.length > 0) setSelectedSoc(payload.geography[0].soc_code);
      })
      .catch((reason: Error) => setError(reason.message));
  }, []);

  const geography = useMemo<Geography[]>(
    () => data?.geography.filter((row) => row.soc_code === selectedSoc) ?? [],
    [data, selectedSoc],
  );

  if (error) {
    return (
      <main className="status-page">
        <p className="kicker">Data unavailable</p>
        <h1>{error}</h1>
        <p>Run the Python build pipeline and copy its summary into frontend/public/data.</p>
      </main>
    );
  }

  if (!data) {
    return (
      <main className="status-page">
        <p className="kicker">Loading evidence</p>
        <h1>Building the labor-market view…</h1>
      </main>
    );
  }

  const maxIntensity = Math.max(...data.top_occupations.map((item) => item.ai_intensity));
  const maxMover = Math.max(...data.fastest_movers.map((item) => item.intensity_change), 1);
  const occupationOptions = Array.from(
    new Map(data.geography.map((row) => [row.soc_code, row.occupation_title])).entries(),
  );

  return (
    <main>
      <header className="hero">
        <nav>
          <a className="brand" href="#top">
            AILO<span>°</span>
          </a>
          <div>
            <a href="#occupations">Occupations</a>
            <a href="#wages">Wages</a>
            <a href="#methods">Methods</a>
          </div>
        </nav>
        <div className="hero-grid" id="top">
          <div>
            <p className="kicker">AI LABOR OBSERVATORY · 2026 EDITION</p>
            <h1>
              Where is AI changing <em>the work?</em>
            </h1>
          </div>
          <div className="hero-note">
            <p>
              A reproducible view of job-posting-derived software demand, occupational
              wages, tasks, education, and geography.
            </p>
            <span>
              {data.releases.current} × BLS OEWS {data.releases.bls_oews}
            </span>
          </div>
        </div>
        <div className="hero-rule" />
      </header>

      <section className="metrics">
        <Metric
          eyebrow="O*NET coverage"
          value={integer.format(data.coverage.onet_occupations)}
          detail="Six-digit occupations with software-skill evidence"
        />
        <Metric
          eyebrow="AI signal"
          value={integer.format(data.headline_metrics.occupations_with_ai_signal)}
          detail="Occupations with at least one classified AI-enabling skill"
        />
        <Metric
          eyebrow="Wage model"
          value={`n = ${integer.format(data.wage_model.observations)}`}
          detail="Complete occupations in the controlled association model"
        />
        <Metric
          eyebrow="Geography"
          value={`${data.coverage.states} states`}
          detail="Comparable BLS wage and employment estimates"
        />
      </section>

      <section className="panel" id="occupations">
        <div className="section-heading">
          <div>
            <p className="kicker">01 · OCCUPATION SIGNAL</p>
            <h2>AI intensity is concentrated—but not confined to tech titles.</h2>
          </div>
          <p>
            The score is a weighted share of O*NET software skills classified as core AI,
            MLOps, data engineering, or analytics. Hot and in-demand flags receive explicit,
            documented weights.
          </p>
        </div>
        <div className="occupation-list">
          {data.top_occupations.slice(0, 12).map((occupation, index) => (
            <article className="occupation-row" key={occupation.soc_code}>
              <span className="rank">{String(index + 1).padStart(2, "0")}</span>
              <div className="occupation-name">
                <strong>{occupation.occupation_title}</strong>
                <small>
                  {occupation.signal_occupation_titles &&
                  occupation.signal_occupation_titles !== occupation.occupation_title
                    ? `Signal: ${occupation.signal_occupation_titles}`
                    : `${occupation.soc_code.slice(0, 2)}-${occupation.soc_code.slice(2)}`}
                </small>
              </div>
              <HorizontalBar value={occupation.ai_intensity} maximum={maxIntensity} />
              <strong className="score">{occupation.ai_intensity.toFixed(1)}</strong>
              <span className="wage">
                {occupation.annual_median_wage
                  ? money.format(occupation.annual_median_wage)
                  : "Suppressed"}
              </span>
            </article>
          ))}
        </div>
      </section>

      <section className="split-panel" id="wages">
        <article className="dark-card">
          <p className="kicker">02 · WAGE ASSOCIATION</p>
          <div className="model-number">
            <span>R²</span>
            <strong>{data.wage_model.r_squared.toFixed(3)}</strong>
          </div>
          <p className="model-copy">{data.wage_model.interpretation}</p>
          <div className="model-stats">
            <span>HC3 robust SE {data.wage_model.standard_error.toFixed(4)}</span>
            <span>p = {data.wage_model.p_value.toFixed(3)}</span>
          </div>
          <p className="caveat">
            Association ≠ causation. Occupation-level aggregation cannot identify an
            individual worker’s return to learning an AI skill.
          </p>
        </article>

        <article className="light-card">
          <p className="kicker">03 · FASTEST MOVERS</p>
          <h3>Change in classified intensity</h3>
          <p className="subtle">
            Comparable occupations between {data.releases.previous} and{" "}
            {data.releases.current}.
          </p>
          <div className="movers">
            {data.fastest_movers.slice(0, 7).map((mover) => (
              <div key={mover.soc_code}>
                <div className="mover-label">
                  <span>{mover.occupation_title}</span>
                  <strong>+{mover.intensity_change.toFixed(1)}</strong>
                </div>
                <HorizontalBar value={mover.intensity_change} maximum={maxMover} accent />
              </div>
            ))}
          </div>
        </article>
      </section>

      <section className="panel">
        <div className="section-heading compact">
          <div>
            <p className="kicker">04 · COMPLEMENTARY TASKS</p>
            <h2>What work travels with higher AI intensity?</h2>
          </div>
          <p>
            Lift compares the share of core tasks in the top AI-intensity quartile with all
            other occupations. It describes co-occurrence, not automation exposure.
          </p>
        </div>
        <div className="task-grid">
          {data.task_complements.map((task) => (
            <article key={task.task_category}>
              <span>{prettyLabel(task.task_category)}</span>
              <strong>{task.lift.toFixed(2)}×</strong>
              <HorizontalBar value={Math.min(task.lift, 2)} maximum={2} accent />
              <small>
                {(task.high_ai_share * 100).toFixed(1)}% of high-AI core tasks
              </small>
            </article>
          ))}
        </div>
      </section>

      <section className="geo-section">
        <div className="section-heading compact">
          <div>
            <p className="kicker">05 · GEOGRAPHY</p>
            <h2>Wages differ sharply across state labor markets.</h2>
          </div>
          <label>
            Featured occupation
            <select value={selectedSoc} onChange={(event) => setSelectedSoc(event.target.value)}>
              {occupationOptions.map(([soc, title]) => (
                <option value={soc} key={soc}>
                  {title}
                </option>
              ))}
            </select>
          </label>
        </div>
        <div className="geo-table">
          <div className="geo-header">
            <span>State</span>
            <span>Median wage</span>
            <span>National index</span>
            <span>Employment</span>
          </div>
          {geography
            .slice()
            .sort((a, b) => (b.wage_index ?? 0) - (a.wage_index ?? 0))
            .map((row) => (
              <div className="geo-row" key={`${row.soc_code}-${row.area_name}`}>
                <strong>{row.area_name}</strong>
                <span>
                  {row.annual_median_wage ? money.format(row.annual_median_wage) : "Suppressed"}
                </span>
                <span>{row.wage_index ? `${row.wage_index.toFixed(0)}` : "—"}</span>
                <span>{row.employment ? integer.format(row.employment) : "Suppressed"}</span>
              </div>
            ))}
        </div>
      </section>

      <section className="methods" id="methods">
        <div>
          <p className="kicker">METHODS & BOUNDARIES</p>
          <h2>A labor-market instrument, not an AI oracle.</h2>
        </div>
        <ol>
          {data.methodology_notes.map((note, index) => (
            <li key={note}>
              <span>{String(index + 1).padStart(2, "0")}</span>
              {note}
            </li>
          ))}
        </ol>
      </section>

      <footer>
        <strong>AI Labor Observatory</strong>
        <span>
          Snapshot generated {new Date(data.generated_at).toLocaleDateString("en-US")} ·
          Open methods, versioned evidence.
        </span>
      </footer>
    </main>
  );
}

export default App;
