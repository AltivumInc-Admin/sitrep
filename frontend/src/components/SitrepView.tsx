import { useEffect, useState } from 'react'
import { api } from '../api'

// Renders the five-paragraph order. Shape mirrors prompts/sitrep_prompt.py SCHEMA.
interface Sitrep {
  date: string
  situation?: { overview: string; changes_since_yesterday?: string[] }
  mission?: { statement: string; why_decisive: string }
  execution?: {
    time_blocks?: { start: string; end: string; label: string; intent: string }[]
    priorities?: Record<string, { title: string; reason: string }[]>
    deliberately_dropped?: { title: string; reason: string }[]
  }
  sustainment?: { energy_plan: string; breaks?: string[] }
  command_signal?: {
    decision_points?: string[]
    blockers_to_escalate?: string[]
    say_no_to?: string[]
    overcommitment_warning?: string | null
  }
  debrief_questions?: string[]
}

export default function SitrepView() {
  const [sitrep, setSitrep] = useState<Sitrep | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const load = async () => {
    try {
      const res = await api.latestSitrep()
      setSitrep(res.sitrep?.body ?? null)
    } catch (e) {
      setError(String(e))
    }
  }

  const generate = async () => {
    setLoading(true)
    setError('')
    try {
      const res = await api.generateSitrep()
      setSitrep(res.sitrep)
    } catch (e) {
      setError(String(e))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  const warn = sitrep?.command_signal?.overcommitment_warning
  return (
    <div className="sitrep">
      <div className="row">
        <h2>{sitrep ? `SITREP ${sitrep.date}` : 'No SITREP yet'}</h2>
        <button onClick={generate} disabled={loading}>
          {loading ? 'Generating…' : 'Generate now'}
        </button>
      </div>
      {error && <p className="error">{error}</p>}
      {!sitrep && !loading && (
        <p className="muted">
          Dump tasks in the Tasks tab, then generate your first operations order.
        </p>
      )}
      {sitrep && (
        <>
          <section>
            <h3>1 · Situation</h3>
            <p>{sitrep.situation?.overview}</p>
            <ul>
              {sitrep.situation?.changes_since_yesterday?.map((c, i) => <li key={i}>{c}</li>)}
            </ul>
          </section>
          <section className="mission">
            <h3>2 · Mission</h3>
            <p className="mission-statement">{sitrep.mission?.statement}</p>
            <p className="muted">{sitrep.mission?.why_decisive}</p>
          </section>
          <section>
            <h3>3 · Execution</h3>
            <div className="blocks">
              {sitrep.execution?.time_blocks?.map((b, i) => (
                <div className="block" key={i}>
                  <span className="mono">
                    {b.start}–{b.end}
                  </span>
                  <strong>{b.label}</strong>
                  <span className="muted">{b.intent}</span>
                </div>
              ))}
            </div>
            {(['p1', 'p2', 'p3'] as const).map((p) => (
              <div key={p} className="prio">
                <span className={`tag ${p}`}>{p.toUpperCase()}</span>
                {sitrep.execution?.priorities?.[p]?.map((t, i) => (
                  <span key={i} title={t.reason} className="prio-item">
                    {t.title}
                  </span>
                ))}
              </div>
            ))}
            {!!sitrep.execution?.deliberately_dropped?.length && (
              <div className="dropped">
                <span className="tag drop">DROPPED</span>
                {sitrep.execution.deliberately_dropped.map((d, i) => (
                  <span key={i} className="prio-item muted" title={d.reason}>
                    {d.title}
                  </span>
                ))}
              </div>
            )}
          </section>
          <section>
            <h3>4 · Sustainment</h3>
            <p>{sitrep.sustainment?.energy_plan}</p>
            <ul>{sitrep.sustainment?.breaks?.map((b, i) => <li key={i}>{b}</li>)}</ul>
          </section>
          <section>
            <h3>5 · Command &amp; Signal</h3>
            <ul>
              {sitrep.command_signal?.decision_points?.map((d, i) => (
                <li key={`dp${i}`}>
                  <span className="tag">DP</span> {d}
                </li>
              ))}
              {sitrep.command_signal?.blockers_to_escalate?.map((b, i) => (
                <li key={`bl${i}`}>
                  <span className="tag warn">BLOCKER</span> {b}
                </li>
              ))}
              {sitrep.command_signal?.say_no_to?.map((s, i) => (
                <li key={`no${i}`}>
                  <span className="tag no">SAY NO</span> {s}
                </li>
              ))}
            </ul>
            {warn && String(warn).toLowerCase() !== 'null' && (
              <p className="overcommit">⚠ {warn}</p>
            )}
          </section>
        </>
      )}
    </div>
  )
}
