import { useEffect, useState } from 'react'
import { api, Task } from '../api'

export default function TasksView() {
  const [dump, setDump] = useState('')
  const [tasks, setTasks] = useState<Task[]>([])
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const load = async () => {
    try {
      const res = await api.tasks('open')
      setTasks(res.tasks)
    } catch (e) {
      setError(String(e))
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
    await api.updateTask(id, { status })
    setTasks((ts) => ts.filter((t) => t.id !== id))
  }

  return (
    <div>
      <h2>Brain dump</h2>
      <p className="muted">
        Dump everything on your mind — the triage officer (Nova Lite) splits it into
        scored tasks. No need to structure anything.
      </p>
      <textarea
        rows={5}
        value={dump}
        placeholder="e.g. need to finish the braket cost memo by friday, follow up with the APSU pilot, elo onboarding email still broken…"
        onChange={(e) => setDump(e.target.value)}
      />
      <button onClick={submitDump} disabled={busy}>
        {busy ? 'Triaging…' : 'Triage dump'}
      </button>
      {error && <p className="error">{error}</p>}

      <h2 style={{ marginTop: '2rem' }}>Open tasks ({tasks.length})</h2>
      <table>
        <thead>
          <tr>
            <th>Task</th>
            <th>Project</th>
            <th>U</th>
            <th>I</th>
            <th>Est(h)</th>
            <th>Due</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {tasks.map((t) => (
            <tr key={t.id}>
              <td title={t.triage?.rationale}>{t.title}</td>
              <td className="muted">{t.project ?? '—'}</td>
              <td className="mono">{t.triage?.urgency ?? '—'}</td>
              <td className="mono">{t.triage?.impact ?? '—'}</td>
              <td className="mono">{t.triage?.effort_hours ?? '—'}</td>
              <td className="mono">{t.due ?? '—'}</td>
              <td>
                <button className="mini" onClick={() => mark(t.id, 'done')}>
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
    </div>
  )
}
