import { useState } from 'react'

function AskAI({ playerIds }) {

  const [question, setQuestion] = useState('')
  const [reply, setReply] = useState(null)
  const [loading, setLoading] = useState(false)

  function handleAsk() {
    setLoading(true)
    setReply(null)

    fetch('http://127.0.0.1:5000/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: question, player_ids: playerIds }),
    })
      .then((response) => response.json())
      .then((data) => {
        setReply(data.reply || data.error)
        setLoading(false)
      })
  }

  return (
    <div className="ask-ai">
      <input
        type="text"
        value={question}
        onChange={(event) => setQuestion(event.target.value)}
        placeholder="Ask about your team..."
      />
      <button type="button" onClick={handleAsk} disabled={loading}>
        {loading ? 'Thinking...' : 'Ask'}
      </button>

      {reply && <p className="ask-ai-reply">{reply}</p>}
    </div>
  )
}

export default AskAI
