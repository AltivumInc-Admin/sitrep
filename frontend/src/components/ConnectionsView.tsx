// Connections: the places a day actually lives. Each row states plainly what
// the integration will DO for the user — a planned integration with no answer
// to "how does this help me" has no business being on this list.

interface Connection {
  id: string
  name: string
  kind: string
  why: string
  mark: JSX.Element
}

// Abstract monochrome marks: the console's own visual language, not borrowed
// brand logos (which would clash with the instrument aesthetic and carry
// trademark baggage).
const MARKS: Record<string, JSX.Element> = {
  telegram: (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M2 12.5 21.5 3 15 21l-4-6.5-2 5-1-6.5L2 12.5Z" />
      <path d="m9 13.5 8-8" className="mark-line" />
    </svg>
  ),
  calendar: (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <rect x="3" y="5" width="18" height="16" rx="1.5" />
      <path d="M3 10h18M8 3v4M16 3v4" className="mark-line" />
      <rect x="7" y="13" width="5" height="4" rx="0.5" className="mark-fill" />
    </svg>
  ),
  todoist: (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M4 8.5 7 11l5-5M4 15.5 7 18l5-5" className="mark-line" />
      <path d="M14 6h6M14 13h6" className="mark-line" />
    </svg>
  ),
  slack: (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M9 3v12M15 9v12M3 15h12M9 9h12" className="mark-line" />
    </svg>
  ),
}

const CONNECTIONS: Connection[] = [
  {
    id: 'telegram',
    name: 'Telegram',
    kind: 'chat channel',
    why: 'Text your agent from anywhere and the plan updates: report what you finished, what just landed on you, or ask what is next. The morning brief arrives as a message you can answer back to, not an email you archive.',
    mark: MARKS.telegram,
  },
  {
    id: 'google-calendar',
    name: 'Google Calendar',
    kind: 'read-only',
    why: 'The plan stops fighting your meetings. Time blocks are built around what is already on your calendar, and the drop list accounts for the three hours of calls you forgot you had when you dumped your tasks.',
    mark: MARKS.calendar,
  },
  {
    id: 'todoist',
    name: 'Todoist',
    kind: 'two-way sync',
    why: 'Keep the task pool you already trust. Tasks flow in from Todoist and completions flow back, so you are never maintaining two lists, and the morning plan draws on everything you are actually carrying.',
    mark: MARKS.todoist,
  },
  {
    id: 'slack',
    name: 'Slack',
    kind: 'morning brief',
    why: 'The brief lands where your workday already starts, sent as a direct message at 0530. Mark a block done or ask for a replan without leaving the workspace you were already in.',
    mark: MARKS.slack,
  },
]

export default function ConnectionsView() {
  return (
    <section>
      <div className="view-head">
        <div>
          <h2>Connections</h2>
          <p className="lede">
            Game Plan OS decides your day. These connect that decision to where
            your day actually happens. Every one on this list earns its place by
            answering a question the plan could not answer alone.
          </p>
        </div>
      </div>

      <ul className="conn-list">
        {CONNECTIONS.map((c) => (
          <li key={c.id} className="conn-row">
            <button
              type="button"
              className="conn-main"
              aria-disabled="true"
              aria-describedby={`why-${c.id}`}
              onClick={(e) => e.preventDefault()}
            >
              <span className="conn-mark" aria-hidden="true">
                {c.mark}
              </span>
              <span className="conn-id">
                <span className="conn-name">{c.name}</span>
                <span className="conn-kind">{c.kind}</span>
              </span>
              <span className="conn-status">coming soon</span>
            </button>
            <div className="conn-why-wrap">
              <div className="conn-why">
                <p id={`why-${c.id}`}>{c.why}</p>
              </div>
            </div>
          </li>
        ))}
      </ul>

      <p className="conn-foot">
        Connecting a service is a decision about your data, so each one is
        opt-in, scoped to the least it needs, and disconnectable here. Nothing
        is shared between accounts.
      </p>
    </section>
  )
}
