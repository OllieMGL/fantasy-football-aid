// displays the outcome of a whole-team "Get Recommendations" request - the
// weakest player per position plus a suggested upgrade, or validation errors
function RecommendationsResult({ result }) {
  if (!result) return null // nothing to show until recommendations have been requested

  return (
    <div className="recommendations-result">
      {result.errors && (
        <ul>
          {result.errors.map((error, index) => (
            <li key={index}>{error}</li>
          ))}
        </ul>
      )}

      {result.error && <p>{result.error}</p>}

      {!result.errors &&
        !result.error &&

        Object.entries(result).map(([position, info]) => (
          <div className="recommendation-row" key={position}>
            <h3>{position}</h3>
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
              <p>No better replacement found in a similar price range.</p>
            )}
          </div>
        ))}
    </div>
  )
}

export default RecommendationsResult
