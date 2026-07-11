import { useEffect, useState } from 'react'
import { api } from '../api'

interface Analysis {
  summary: string
  mission_accomplished: boolean
  what_worked?: string[]
  what_slipped?: { item: string; proximate_cause: string }[]
  candidate_preferences?: { text: string; confidence: string }[]
  tomorrow_note?: string
}

export default function DebriefView() {
  const [questions, setQuestions] = useState<string[]>([])
  const [answers, setAnswers] = useState<Record<string, string>>({})
  const [analysis, setAnalysis] = useState<Analysis | null>(null)
  const [busy, setBusy] = useState(false)
  const [loaded, setLoaded] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    api
      .latestSitrep()
      .then((res) => setQuestions(res.sitrep?.body?.debrief_questions ?? []))
      .catch((e) => setError(String(e)))
      .finally(() => setLoaded(true))
  }, [])

  const submit = async () => {
    setBusy(true)
    setError('')
    try {
      const res = await api.debrief(answers)
      setAnalysis(res.analysis)
    } catch (e) {
      setError(String(e))
    } finally {
      setBusy(false)
    }
  }

  if (analysis) {
    return (
      <div>
        <div className="view-head">
          <div>
            <span className="kicker">after-action review</span>
            <h2>How today actually went</h2>
          </div>
          <button className="ghost" onClick={() => setAnalysis(null)}>
            Back to questions
          </button>
        </div>

        <p className={`verdict ${analysis.mission_accomplished ? 'ok' : 'miss'} rise`}>
          {analysis.mission_accomplished
            ? 'Mission accomplished'
            : 'Mission not accomplished'}
        </p>
        <p className="rise" style={{ ['--i' as string]: 1 }}>
          {analysis.summary}
        </p>

        {!!analysis.what_worked?.length && (
          <section className="para rise" style={{ ['--i' as string]: 2 }}>
            <div className="para-head">
              <span className="para-title">What worked</span>
            </div>
            <ul>
              {analysis.what_worked.map((w, i) => (
                <li key={i}>{w}</li>
              ))}
            </ul>
          </section>
        )}

        {!!analysis.what_slipped?.length && (
          <section className="para rise" style={{ ['--i' as string]: 3 }}>
            <div className="para-head">
              <span className="para-title">What slipped</span>
              <span className="para-plain">and the immediate cause, not the excuse</span>
            </div>
            <ul>
              {analysis.what_slipped.map((s, i) => (
                <li key={i}>
                  {s.item} <span className="dim">&mdash; {s.proximate_cause}</span>
                </li>
              ))}
            </ul>
          </section>
        )}

        {!!analysis.candidate_preferences?.length && (
          <div className="learned rise" style={{ ['--i' as string]: 4 }}>
            <div className="para-head">
              <span className="para-title">What it learned about you</span>
              <span className="para-plain">
                only patterns with repeated evidence are kept
              </span>
            </div>
            {analysis.candidate_preferences.map((p, i) => (
              <div className="learned-item" key={i}>
                <span className={`tag ${p.confidence === 'high' ? 'ok' : 'p3'}`}>
                  {p.confidence}
                </span>
                <span>
                  {p.text}
                  {p.confidence === 'high' && (
                    <span className="saved">
                      {' '}
                      &mdash; saved to your profile; it will shape tomorrow&rsquo;s plan
                    </span>
                  )}
                </span>
              </div>
            ))}
          </div>
        )}

        {analysis.tomorrow_note && (
          <p className="dim rise" style={{ ['--i' as string]: 5 }}>
            Tomorrow&rsquo;s planner reads this first: &ldquo;{analysis.tomorrow_note}&rdquo;
          </p>
        )}
      </div>
    )
  }

  return (
    <div>
      <div className="view-head">
        <div>
          <span className="kicker">evening debrief</span>
          <h2>Three questions about today</h2>
          <p className="lede">
            Generated from this morning&rsquo;s game plan, so they are about your
            actual plan, not your day in general. Honest answers are what make
            tomorrow&rsquo;s plan smarter; this is the learning loop.
          </p>
        </div>
      </div>

      {loaded && questions.length === 0 && !error && (
        <div className="empty">
          <span className="kicker">no game plan today</span>
          Generate a game plan first; its three debrief questions will appear
          here in the evening.
        </div>
      )}

      {questions.map((q, i) => (
        <div key={i} className="q-card rise" style={{ ['--i' as string]: i }}>
          <span className="q-num">question {i + 1} of {questions.length}</span>
          <label htmlFor={`q${i + 1}`}>{q}</label>
          <textarea
            id={`q${i + 1}`}
            rows={3}
            value={answers[`q${i + 1}`] ?? ''}
            onChange={(e) => setAnswers((a) => ({ ...a, [`q${i + 1}`]: e.target.value }))}
          />
        </div>
      ))}

      {questions.length > 0 && (
        <button className="primary" onClick={submit} disabled={busy}>
          {busy ? 'Reviewing' : 'Submit debrief'}
        </button>
      )}
      {busy && (
        <p className="status-line" role="status">
          <span className="pulse" aria-hidden="true" />
          Comparing the plan against how the day actually went&hellip;
        </p>
      )}
      {error && <p className="error">{error}</p>}
    </div>
  )
}
