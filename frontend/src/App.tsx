import { useEffect, useState } from 'react'
import { getKey, setKey } from './api'
import SitrepView from './components/SitrepView'
import TasksView from './components/TasksView'
import DebriefView from './components/DebriefView'

type Tab = 'brief' | 'tasks' | 'debrief'

function Clock() {
  const [now, setNow] = useState(new Date())
  useEffect(() => {
    const t = setInterval(() => setNow(new Date()), 1000)
    return () => clearInterval(t)
  }, [])
  const hh = String(now.getHours()).padStart(2, '0')
  const mm = String(now.getMinutes()).padStart(2, '0')
  const ss = String(now.getSeconds()).padStart(2, '0')
  const tz = Intl.DateTimeFormat().resolvedOptions().timeZone
  return (
    <span className="clock" title="Your local time">
      {hh}:{mm}:{ss} {tz}
    </span>
  )
}

function Gate({ onEnter }: { onEnter: () => void }) {
  const [value, setValue] = useState('')
  const submit = () => {
    if (!value.trim()) return
    setKey(value.trim())
    onEnter()
  }
  return (
    <div className="gate-wrap">
      <div className="gate">
        <div className="brand rise" style={{ ['--i' as string]: 0 }}>
          <span className="brand-mark" aria-hidden="true" />
          <span className="brand-name">GAME PLAN OS</span>
          <span className="brand-sub">your daily game plan</span>
        </div>
        <h1 className="rise" style={{ ['--i' as string]: 1 }}>
          A one-page game plan for the day, written for you every morning.
        </h1>
        <p className="intro rise" style={{ ['--i' as string]: 2 }}>
          Game Plan OS reads your open tasks, what it has learned about how you
          work, and how yesterday actually went. Then it makes decisions: one
          mission for the day, a timed plan with deliberate breathing room, and
          a short list of things it chose to drop, with reasons. In the evening
          it asks three questions and learns from your answers.
        </p>
        <p className="term rise" style={{ ['--i' as string]: 3 }}>
          The format is borrowed, in spirit, from the military five-paragraph
          operations order: where things stand, one mission, the plan, pacing,
          and the calls you may need to make. No military background needed;
          it is simply a disciplined way to decide.
        </p>
        <div className="key-row rise" style={{ ['--i' as string]: 4 }}>
          <input
            type="password"
            value={value}
            placeholder="access key"
            aria-label="Access key"
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && submit()}
          />
          <button className="primary" onClick={submit}>
            Enter
          </button>
        </div>
        <p className="key-hint rise" style={{ ['--i' as string]: 5 }}>
          This is the key you chose when deploying the backend. It is stored
          only in this browser.
        </p>
      </div>
    </div>
  )
}

export default function App() {
  const [tab, setTab] = useState<Tab>('brief')
  const [authed, setAuthed] = useState(Boolean(getKey()))

  useEffect(() => {
    document.title = 'Game Plan OS — Your Daily Game Plan'
  }, [])

  if (!authed) return <Gate onEnter={() => setAuthed(true)} />

  const signOut = () => {
    setKey('')
    setAuthed(false)
  }

  return (
    <div className="shell">
      <header className="top">
        <div className="brand">
          <span className="brand-mark" aria-hidden="true" />
          <span className="brand-name">GAME PLAN OS</span>
          <span className="brand-sub">your daily game plan</span>
        </div>
        <div className="top-right">
          <Clock />
          <nav className="tabs" aria-label="Views">
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
        </div>
      </header>
      <main>
        {tab === 'brief' && <SitrepView />}
        {tab === 'tasks' && <TasksView />}
        {tab === 'debrief' && <DebriefView />}
      </main>
      <footer className="bottom">
        <span>
          Amazon Bedrock (Nova) &middot; Lambda &middot; DynamoDB &middot;
          EventBridge Scheduler &middot; SES &middot; Amplify Hosting
        </span>
        <span>
          <a href="https://github.com/AltivumInc-Admin/gameplan-os">source</a>
          {' '}&middot;{' '}
          <button
            className="mini ghost"
            onClick={signOut}
            title="Forget the access key stored in this browser"
          >
            change key
          </button>
        </span>
      </footer>
    </div>
  )
}
