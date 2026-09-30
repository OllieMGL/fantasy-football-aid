import { useState } from 'react'

function AskAI({ playerIds, budget, onApplyChanges }) {

  const [question, setQuestion] = useState('')
  const [reply, setReply] = useState(null)
  const [loading, setLoading] = useState(false)

  const [proposedChanges, setProposedChanges] = useState(null)

  function handleAsk() {
    // the box is cleared straight away, so "asked" holds onto the text
    const asked = question.trim()

    if (!asked) return 

    setLoading(true)
    setReply(null)
    setProposedChanges(null)
    setQuestion('')

    fetch('http://127.0.0.1:5000/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: asked, player_ids: playerIds, budget }),
    })
      .then((response) => response.json())
      .then((data) => {
        setReply(data.reply || data.error)
        setProposedChanges(data.proposed_changes || null)
        setLoading(false)
      })
      .catch(() => {
        setReply("Can't reach the server. Is the backend running?")
        setLoading(false) // otherwise it stays stuck on "Thinking..."
      })
  }

  function handleApply() {
    onApplyChanges(proposedChanges)
    setProposedChanges(null)
  }

  return (
    <div className="ask-ai">
      <p className="ask-ai-title">Ask about your team</p>

      <div className="ask-ai-messages">
        {reply ? (
          <p className="ask-ai-reply">{reply}</p>
        ) : (
          <p className="ask-ai-placeholder">
            Ask a question about your squad - e.g. "who should I bring in for defense?"
          </p>
        )}

        {proposedChanges && (
          <div className="ask-ai-changes">
            <ul>
              {proposedChanges.map((change) => (
                <li key={change.in_id}>
                  {change.out_name ? `Out: ${change.out_name} → ` : ''}
                  In: {change.in_name} (£{change.in_price}m)
                </li>
              ))}
            </ul>

            <button type="button" onClick={handleApply} className="primary-button-sm">
              Apply these changes
            </button>
          </div>
        )}
      </div>

      <div className="ask-ai-input-row">
        <input
          type="text"
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          onKeyDown={(event) => event.key === 'Enter' && handleAsk()}
          placeholder="Ask about your team..."
        />
        <button type="button" onClick={handleAsk} disabled={loading}>
          {loading ? '...' : 'Ask'}
        </button>
      </div>
    </div>
  )
}

export default AskAI
