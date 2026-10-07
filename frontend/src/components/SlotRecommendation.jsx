import { useState } from 'react'

function SlotRecommendation({ position, otherPlayerIds, budget, onSelectPlayer }) {
  const [result, setResult] = useState(null)

  function handleRecommend() {
    fetch(`${import.meta.env.VITE_API_URL}/recommend-slot`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ player_ids: otherPlayerIds, position, budget }),
    })
      .then((response) => response.json())
      .then((data) => setResult(data))
      .catch(() => setResult({ error: "Can't reach the server" }))
  }

  return (
    <div className="slot-recommendation">
      <button type="button" onClick={handleRecommend} className="secondary-button">
        Recommend a player for this slot
      </button>

      {result && (
        <div className="slot-recommendation-result">
          {result.error && <p>{result.error}</p>}

          {result.suggestions && (
            result.suggestions.length > 0 ? (
              <ul className="player-list">
                {result.suggestions.map((player) => (
                  <li key={player.id}>
                    <button type="button" onClick={() => onSelectPlayer(player)}>
                      {player.first_name} {player.second_name} - £{player.now_cost}m (score: {player.score})
                    </button>
                  </li>
                ))}
              </ul>
            ) : (
              <p>
                No suitable player found within the remaining budget (max £
                {result.max_price_for_slot}m for this slot).
              </p>
            )
          )}
        </div>
      )}
    </div>
  )
}

export default SlotRecommendation
