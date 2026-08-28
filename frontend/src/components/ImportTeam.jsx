import { useState } from 'react'

function ImportTeam({ onImport }) {

  const [teamId, setTeamId] = useState('')
  const [error, setError] = useState(null)

  function handleImport() {
    setError(null)

    fetch(`http://127.0.0.1:5000/import-team/${teamId}`)
      // fetch only rejects on network failure, not on 404/409 - so we pair the
      // parsed body with response.ok here to know which case we're in below
      .then((response) => response.json().then((data) => ({ ok: response.ok, data })))
      .then(({ ok, data }) => {
        if (!ok) {
          setError(data.error)
          return
        }

        onImport(data.player_ids, data.bank)
      })
  }

  return (
    <div className="import-team">
      <input
        type="text"
        inputMode="numeric"
        value={teamId}
        onChange={(event) => setTeamId(event.target.value)}
        placeholder="FPL Team ID"
      />
      <button type="button" onClick={handleImport}>
        Import Team
      </button>

      {error && <p className="import-error">{error}</p>}
    </div>
  )
}

export default ImportTeam
