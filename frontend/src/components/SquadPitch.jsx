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

  // maps a slot id like "DEF-2" to the player object filling it - empty
  // object means no slots have been filled yet
  const [squad, setSquad] = useState({})

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

  return (
    <div className="squad-pitch">
      {Object.entries(FORMATION).map(([position, count]) => (

        // for each position create x shirt icons
        <div className="position-row" key={position}>
          {Array.from({ length: count }).map((_, index) => (

            <ShirtSlot
              key={`${position}-${index}`}
              position={position}
              onClick={() => setOpenSlot({ position, index })}
            />
          ))}

        </div>
      ))}

      {openSlot && (
        <div className="picker-panel">
          <p>
            Picking a player for {openSlot.position} (slot {openSlot.index + 1})
          </p>
          <ul className="player-list">
            {playersForOpenSlot.map((player) => (
              <li key={player.id}>
                {player.first_name} {player.second_name} - £{player.now_cost}m
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
