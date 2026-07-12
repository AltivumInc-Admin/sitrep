import { useEffect, useRef, useState } from 'react'
import { api, ChatMessage } from '../api'

// Plain-language receipts for the verbs the agent can run. Read-only tools
// are deliberately absent: reading is not worth announcing.
const TOOL_LABELS: Record<string, string> = {
  add_tasks: 'added tasks',
  complete_task: 'closed a task',
  reopen_task: 'reopened a task',
  drop_task: 'dropped a task',
  mark_block: 'marked a block',
  replan_day: 'replanned the rest of today',
  generate_plan: 'built a plan',
}

interface Row extends ChatMessage {
  receipt?: string
  failed?: boolean
}

export default function AgentDock() {
  const [open, setOpen] = useState(false)
  const [hydrated, setHydrated] = useState(false)
  const [rows, setRows] = useState<Row[]>([])
  const [draft, setDraft] = useState('')
  const [busy, setBusy] = useState(false)
  const scroller = useRef<HTMLDivElement | null>(null)
  const input = useRef<HTMLInputElement | null>(null)

  // Server history survives reloads (it is the same conversation the agent
  // sees); pull it the first time the dock opens.
  useEffect(() => {
    if (!open || hydrated) return
    api
      .agentHistory()
      .then((res) => setRows(res.messages))
      .catch(() => undefined)
      .finally(() => setHydrated(true))
  }, [open, hydrated])

  useEffect(() => {
    if (open) window.setTimeout(() => input.current?.focus(), 50)
  }, [open])

  useEffect(() => {
    scroller.current?.scrollTo({ top: scroller.current.scrollHeight })
  }, [rows, busy, open])

  const send = async () => {
    const message = draft.trim()
    if (!message || busy) return
    setDraft('')
    setRows((r) => [...r, { role: 'user', text: message }])
    setBusy(true)
    try {
      const turn = await api.agentChat(message)
      const receipt = turn.tools_used
        .map((t) => TOOL_LABELS[t])
        .filter(Boolean)
        .join(', ')
      setRows((r) => [...r, { role: 'assistant', text: turn.reply, receipt }])
      if (turn.mutated) window.dispatchEvent(new Event('sitrep-data-changed'))
    } catch (e) {
      const detail = String(e instanceof Error ? e.message : e)
      const timedOut = /50[34]|time/i.test(detail)
      setRows((r) => [
        ...r,
        {
          role: 'assistant',
          failed: true,
          text: timedOut
            ? 'That took longer than the connection allows. If you asked for a change it may still have gone through; give it a few seconds, then check the plan.'
            : `That did not go through: ${detail}`,
        },
      ])
    } finally {
      setBusy(false)
      input.current?.focus()
    }
  }

  const reset = async () => {
    if (busy) return
    setRows([])
    try {
      await api.agentReset()
    } catch {
      /* a failed reset just means old context lingers server-side */
    }
  }

  if (!open) {
    return (
      <button className="dock-pill" onClick={() => setOpen(true)} aria-label="Open the agent">
        <span className="dock-dot" aria-hidden="true" />
        Agent
      </button>
    )
  }

  return (
    <section className="dock" aria-label="Agent conversation">
      <header className="dock-head">
        <div>
          <span className="dock-title">
            <span className="dock-dot" aria-hidden="true" />
            Agent
          </span>
          <span className="dock-sub">Report in plain words; your plan updates.</span>
        </div>
        <div className="dock-actions">
          <button className="mini ghost" onClick={reset} disabled={busy} title="Forget this conversation and start fresh">
            reset
          </button>
          <button className="mini ghost" onClick={() => setOpen(false)} aria-label="Collapse the agent panel">
            close
          </button>
        </div>
      </header>
      <div className="dock-scroll" ref={scroller}>
        {rows.length === 0 && !busy && (
          <p className="dock-empty">
            Try: &ldquo;What&rsquo;s my plan?&rdquo; &mdash; &ldquo;I finished the memo&rdquo; &mdash;
            &ldquo;A client call just landed at 2pm, replan around it.&rdquo;
          </p>
        )}
        {rows.map((m, i) => (
          <div key={i} className={`dock-msg ${m.role}${m.failed ? ' failed' : ''}`}>
            <p>{m.text}</p>
            {m.receipt ? <span className="dock-receipt">{m.receipt}</span> : null}
          </div>
        ))}
        {busy && (
          <div className="dock-msg assistant dock-busy" aria-live="polite">
            <p>Working&hellip;</p>
          </div>
        )}
      </div>
      <form
        className="dock-form"
        onSubmit={(e) => {
          e.preventDefault()
          send()
        }}
      >
        <input
          ref={input}
          id="agent-message"
          name="agent-message"
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder="Report in: done, new, or changed"
          autoComplete="off"
          maxLength={4000}
          onKeyDown={(e) => {
            if (e.key === 'Escape') setOpen(false)
          }}
        />
        <button type="submit" className="mini" disabled={busy || !draft.trim()}>
          Send
        </button>
      </form>
    </section>
  )
}
