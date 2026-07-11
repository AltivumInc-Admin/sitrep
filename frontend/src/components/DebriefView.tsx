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
  const [error, setError] = useState('')

  useEffect(() => {
    api
      .latestSitrep()
      .then((res) => setQuestions(res.sitrep?.body?.debrief_questions ?? []))
      .catch((e) => setError(String(e)))
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
        <h2>After-action review</h2>
        <p className={analysis.mission_accomplished ? 'ok' : 'warn-text'}>
          {analysis.mission_accomplished ? '✓ Mission accomplished' : '✗ Mission not accomplished'}
        </p>
        <p>{analysis.summary}</p>
        {!!analysis.what_slipped?.length && (
          <>
            <h3>What slipped</h3>
            <ul>
              {analysis.what_slipped.map((s, i) => (
                <li key={i}>
                  {s.item} <span className="muted">— {s.proximate_cause}</span>
                </li>
              ))}
            </ul>
          </>
        )}
        {!!analysis.candidate_preferences?.length && (
          <>
            <h3>What the agent learned about you</h3>
            <ul>
              {analysis.candidate_preferences.map((p, i) => (
                <li key={i}>
                  <span className={`tag ${p.confidence === 'high' ? 'p1' : ''}`}>
                    {p.confidence}
                  </span>{' '}
                  {p.text}
                  {p.confidence === 'high' && (
                    <span className="muted"> → saved to profile, shapes tomorrow's brief</span>
                  )}
                </li>
              ))}
            </ul>
          </>
        )}
        {analysis.tomorrow_note && (
          <p className="muted">Tomorrow's planner will read first: “{analysis.tomorrow_note}”</p>
        )}
      </div>
    )
  }

  return (
    <div>
      <h2>Evening debrief</h2>
      <p className="muted">
        Three questions generated from this morning's order. Honest answers make
        tomorrow's SITREP smarter — this is the learning loop.
      </p>
      {questions.length === 0 && <p className="muted">No SITREP today — nothing to debrief.</p>}
      {questions.map((q, i) => (
        <div key={i} className="q">
          <label>{q}</label>
          <textarea
            rows={3}
            value={answers[`q${i + 1}`] ?? ''}
            onChange={(e) => setAnswers((a) => ({ ...a, [`q${i + 1}`]: e.target.value }))}
          />
        </div>
      ))}
      {questions.length > 0 && (
        <button onClick={submit} disabled={busy}>
          {busy ? 'Analyzing…' : 'Submit debrief'}
        </button>
      )}
      {error && <p className="error">{error}</p>}
    </div>
  )
}
