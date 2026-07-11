import { useEffect, useState } from 'react'
import { api, Task } from '../api'

function Meter({ value, hot }: { value?: number; hot?: boolean }) {
  if (!value) return <span className="faint mono">&mdash;</span>
  const v = Math.max(0, Math.min(5, Math.round(value)))
  return (
    <span
      className={`meter${hot && v >= 4 ? ' hot' : ''}`}
      role="img"
      aria-label={`${v} out of 5`}
      title={`${v} / 5`}
    >
      {[1, 2, 3, 4, 5].map((i) => (
        <i key={i} className={i <= v ? 'on' : ''} />
      ))}
    </span>
  )
}

export default function TasksView() {
  const [dump, setDump] = useState('')
  const [tasks, setTasks] = useState<Task[]>([])
  const [busy, setBusy] = useState(false)
  const [loaded, setLoaded] = useState(false)
  const [error, setError] = useState('')

  const load = async () => {
    try {
      const res = await api.tasks('open')
      setTasks(res.tasks)
    } catch (e) {
      setError(String(e))
    } finally {
      setLoaded(true)
    }
  }

  useEffect(() => {
    load()
  }, [])

  const submitDump = async () => {
    if (!dump.trim()) return
    setBusy(true)
    setError('')
    try {
      await api.dump(dump.trim())
      setDump('')
      await load()
    } catch (e) {
      setError(String(e))
    } finally {
      setBusy(false)
    }
  }

  const mark = async (id: string, status: 'done' | 'dropped') => {
    try {
      await api.updateTask(id, { status })
      setTasks((ts) => ts.filter((t) => t.id !== id))
    } catch (e) {
      setError(String(e))
    }
  }

  return (
    <div>
      <div className="view-head">
        <div>
          <span className="kicker">capture</span>
          <h2>Write it all down</h2>
          <p className="lede">
            Half-formed is fine. A fast model splits whatever you write into
            separate tasks and scores each one for urgency, impact, and honest
            effort, so nothing needs to be structured up front.
          </p>
        </div>
      </div>
      <textarea
        rows={5}
        value={dump}
        aria-label="Brain dump"
        placeholder="e.g. finish the cost memo by friday, follow up with the pilot program, onboarding email still broken, book flights for the conference sometime..."
        onChange={(e) => setDump(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) submitDump()
        }}
      />
      <button className="primary" onClick={submitDump} disabled={busy}>
        {busy ? 'Sorting' : 'Sort into tasks'}
      </button>
      {busy && (
        <p className="status-line" role="status">
          <span className="pulse" aria-hidden="true" />
          Splitting your notes into scored tasks&hellip;
        </p>
      )}
      {error && <p className="error">{error}</p>}

      <div className="view-head" style={{ marginTop: '2.6rem' }}>
        <div>
          <span className="kicker">open tasks &middot; {tasks.length}</span>
          <h2>The pool the planner draws from</h2>
        </div>
      </div>

      {loaded && tasks.length === 0 ? (
        <div className="empty">
          <span className="kicker">nothing here yet</span>
          Everything you write above becomes a scored task in this list, and
          tomorrow&rsquo;s game plan is built from it.
        </div>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Task</th>
              <th>Project</th>
              <th title="Time pressure, 1 to 5">Urgency</th>
              <th title="Consequence of doing it, 1 to 5">Impact</th>
              <th title="Honest effort estimate, in hours">Est. hours</th>
              <th>Due</th>
              <th aria-label="Actions"></th>
            </tr>
          </thead>
          <tbody>
            {tasks.map((t) => (
              <tr key={t.id}>
                <td>
                  {t.title}
                  {t.triage?.rationale && <span className="notes">{t.triage.rationale}</span>}
                </td>
                <td className="dim">{t.project ?? <span className="faint">&mdash;</span>}</td>
                <td>
                  <Meter value={t.triage?.urgency} hot />
                </td>
                <td>
                  <Meter value={t.triage?.impact} />
                </td>
                <td className="mono">{t.triage?.effort_hours ?? <span className="faint">&mdash;</span>}</td>
                <td className="mono">{t.due ?? <span className="faint">&mdash;</span>}</td>
                <td className="actions">
                  <button className="mini primary" onClick={() => mark(t.id, 'done')}>
                    done
                  </button>
                  <button className="mini ghost" onClick={() => mark(t.id, 'dropped')}>
                    drop
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}
