function RecommendationsResult({ result, onClose }) {
  if (!result) return null // nothing to show until recommendations have been requested

  // early return, so the loop below never tries to read an error string as if
  // it were a position entry
  if (result.error) {
    return (
      <div className="recommendations-result">
        <p>{result.error}</p>

        <button type="button" onClick={onClose}>
          Close
        </button>
      </div>
    )
  }

  return (
    <div className="recommendations-result">
      {Object.entries(result).map(([position, info]) => (
        <div className="recommendation-row" key={position}>
          <h3>{position}</h3>

          {info.action === 'fill' ? (
            <>
              <p className="recommendation-meta">
                {info.filled} of {info.required} picked - {info.missing} to add
              </p>

              {info.suggestions.length > 0 ? (
                <ul className="recommendation-suggestions">
                  {info.suggestions.map((player) => (
                    <li key={player.id}>
                      {player.first_name} {player.second_name} - £{player.now_cost}m (score:{' '}
                      {player.score})
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="recommendation-empty">
                  Nothing fits the £{info.max_price_for_slot}m left for this slot.
                </p>
              )}
            </>
          ) : (
            <>
              <p>
                Weakest: {info.current_player.first_name} {info.current_player.second_name} -{' '}
                {info.current_score}
              </p>

              {info.suggested_replacement ? (
                <p>
                  Suggested upgrade: {info.suggested_replacement.first_name}{' '}
                  {info.suggested_replacement.second_name} - {info.suggested_score} (£
                  {info.suggested_replacement.now_cost}m)
                </p>
              ) : (
                <p className="recommendation-empty">
                  No better replacement found that you can afford.
                </p>
              )}
            </>
          )}
        </div>
      ))}

      <button type="button" onClick={onClose}>
        Close
      </button>
    </div>
  )
}

export default RecommendationsResult
