import { useState, useEffect } from 'react'
import ShirtSlot from './ShirtSlot'

// how many slots to render for each position
const FORMATION = {
  GKP: 2,
  DEF: 5,
  MID: 5,
  FWD: 3,
}

function SquadPitch() {

  // tracks which shirt is currently being edited, e.g. { position: "DEF", index: 2 }
  const [openSlot, setOpenSlot] = useState(null)

  // holds every player fetched from the backend, once loaded
  const [players, setPlayers] = useState([])

  const [squad, setSquad] = useState({})

  const [scoreResult, setScoreResult] = useState(null)

  useEffect(() => {
    fetch('http://127.0.0.1:5000/players')
      .then((response) => response.json())
      .then((data) => setPlayers(data))
  }, [])

  // the players eligible for whichever slot is currently open, ordered by price descending
  const playersForOpenSlot = openSlot
    ? players // if open slot is true...
        .filter((player) => player.position === openSlot.position)
        .sort((a, b) => b.now_cost - a.now_cost)
    : [] // value if openSlot is empty


  // fills the currently open slot with the chosen player, then closes the player list
  function handleSelectPlayer(player) {
    const slotId = `${openSlot.position}-${openSlot.index}`

    setSquad({ ...squad, [slotId]: player })
    console.log('selected player for', slotId, ':', player)
    setOpenSlot(null)
  }

  function handleScoreTeam() {
    const playerIds = Object.values(squad)
      .filter(Boolean) // filter for selected valid players (no empty ones)
      .map((player) => player.id)

    fetch('http://127.0.0.1:5000/score-team', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ player_ids: playerIds }),
    })
      .then((response) => response.json())
      .then((data) => setScoreResult(data))
  }

  return (
    <div className="squad-pitch">
      {Object.entries(FORMATION).map(([position, count]) => (

        // for each position create x shirt icons
        <div className="position-row" key={position}>
          {Array.from({ length: count }).map((_, index) => (

            <ShirtSlot
              key={`${position}-${index}`}
              position={position}
              player={squad[`${position}-${index}`]}
              onClick={() => setOpenSlot({ position, index })}
            />
          ))}

        </div>
      ))}

      <button type="button" onClick={handleScoreTeam}>
        Score My Team
      </button>

      {scoreResult && (
        <div className="score-result">
          {scoreResult.score !== undefined && <p>Team score: {scoreResult.score}/100</p>}

          {scoreResult.errors && (
            <ul>
              {scoreResult.errors.map((error, index) => (
                <li key={index}>{error}</li>
              ))}
            </ul>
          )}

          {scoreResult.error && <p>{scoreResult.error}</p>}
        </div>
      )}

      {openSlot && (
        <div className="picker-panel">
          <p>
            Picking a player for {openSlot.position} (slot {openSlot.index + 1})
          </p>
          <ul className="player-list">
            {playersForOpenSlot.map((player) => (
              <li key={player.id}>
                <button type="button" onClick={() => handleSelectPlayer(player)}>
                  {player.first_name} {player.second_name} - £{player.now_cost}m
                </button>
              </li>
            ))}
          </ul>
          <button type="button" onClick={() => setOpenSlot(null)}>
            Close
          </button>
        </div>
      )}
    </div>
  )
}

export default SquadPitch
