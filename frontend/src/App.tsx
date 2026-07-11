import { useEffect, useState } from 'react'
import { api, getKey, setKey } from './api'
import SitrepView from './components/SitrepView'
import TasksView from './components/TasksView'
import DebriefView from './components/DebriefView'

type Tab = 'brief' | 'tasks' | 'debrief'

export default function App() {
  const [tab, setTab] = useState<Tab>('brief')
  const [keyInput, setKeyInput] = useState(getKey())
  const [authed, setAuthed] = useState(Boolean(getKey()))

  useEffect(() => {
    document.title = 'SITREP — Daily Operations Order'
  }, [])

  if (!authed) {
    return (
      <div className="gate">
        <h1>SITREP</h1>
        <p className="muted">Personal AI operations officer. Enter your access key.</p>
        <input
          type="password"
          value={keyInput}
          placeholder="x-sitrep-key"
          onChange={(e) => setKeyInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && keyInput.trim()) {
              setKey(keyInput.trim())
              setAuthed(true)
            }
          }}
        />
        <button
          onClick={() => {
            if (keyInput.trim()) {
              setKey(keyInput.trim())
              setAuthed(true)
            }
          }}
        >
          Enter
        </button>
      </div>
    )
  }

  return (
    <div className="shell">
      <header>
        <div className="brand">
          <span className="brand-mark">▲</span> SITREP
          <span className="brand-sub">daily operations order</span>
        </div>
        <nav>
          <button className={tab === 'brief' ? 'active' : ''} onClick={() => setTab('brief')}>
            Brief
          </button>
          <button className={tab === 'tasks' ? 'active' : ''} onClick={() => setTab('tasks')}>
            Tasks
          </button>
          <button className={tab === 'debrief' ? 'active' : ''} onClick={() => setTab('debrief')}>
            Debrief
          </button>
        </nav>
      </header>
      <main>
        {tab === 'brief' && <SitrepView />}
        {tab === 'tasks' && <TasksView />}
        {tab === 'debrief' && <DebriefView />}
      </main>
      <footer className="muted">
        Built on AWS — Bedrock (Nova) · Lambda · DynamoDB · EventBridge · SES · Amplify
      </footer>
    </div>
  )
}
