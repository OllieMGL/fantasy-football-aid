import { useState, useEffect } from 'react'
import PitchGrid from './PitchGrid'
import PlayerSelector from './PlayerSelector'
import SlotRecommendation from './SlotRecommendation'
import RecommendationsResult from './RecommendationsResult'
import ImportTeam from './ImportTeam'


function buildSquadFromPlayerIds(playerIds, playersList) {
  const positionCounts = { GKP: 0, DEF: 0, MID: 0, FWD: 0 }
  const newSquad = {}

  for (const id of playerIds) {
    const player = playersList.find((candidate) => candidate.id === id)

    const index = positionCounts[player.position]
    newSquad[`${player.position}-${index}`] = player //a ssigns the full player object to that slot in newSquad
    positionCounts[player.position] += 1
  }

  return newSquad
}

function SquadPitch() {

  // tracks which shirt is currently being edited, e.g. { position: "DEF", index: 2 }
  const [openSlot, setOpenSlot] = useState(null)

  // holds every player fetched from the backend, once loaded
  const [players, setPlayers] = useState([])
  const [squad, setSquad] = useState({})

  const [scoreResult, setScoreResult] = useState(null)
  const [recommendationsResult, setRecommendationsResult] = useState(null)

  const [importedBank, setImportedBank] = useState(null) //imported team bank balance

  useEffect(() => {
    fetch('http://127.0.0.1:5000/players')
      .then((response) => response.json())
      .then((data) => setPlayers(data))
  }, [])

  const amountSpent = Object.values(squad)
    .filter(Boolean)
    // .reduce takes the array down to one value ==> total money spent
    .reduce((total, player) => total + player.now_cost, 0) // inital value is 0

  const budgetRemaining = 100 - amountSpent

  // every filled slot EXCEPT the one currently open - passed to SlotRecommendation
  // so the backend knows how much budget is genuinely free for this slot
  const otherPlayerIdsForOpenSlot = openSlot
    ? Object.entries(squad)
        .filter(([slotId, player]) => player && slotId !== `${openSlot.position}-${openSlot.index}`)
        .map(([, player]) => player.id)
    : []

  // fills the currently open slot with the chosen player, then closes the player list
  function handleSelectPlayer(player) {
    const slotId = `${openSlot.position}-${openSlot.index}`

    setSquad({ ...squad, [slotId]: player })
    setImportedBank(null) // no longer neeed the imported bank balance - redudant as user has made changes 
    console.log('selected player for', slotId, ':', player)
    setOpenSlot(null)
  }

  function getPlayerIds() {
    return Object.values(squad)
      .filter(Boolean) // filter for selected valid players (no empty ones)
      .map((player) => player.id)
  }

  function handleScoreTeam() {
    fetch('http://127.0.0.1:5000/score-team', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ player_ids: getPlayerIds() }),
    })
      .then((response) => response.json())
      .then((data) => setScoreResult(data))
  }

  function handleGetRecommendations() {
    fetch('http://127.0.0.1:5000/recommendations', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ player_ids: getPlayerIds() }),
    })
      .then((response) => response.json())
      .then((data) => setRecommendationsResult(data))
  }

  function handleImportTeam(playerIds, bank) {
    setSquad(buildSquadFromPlayerIds(playerIds, players))
    setImportedBank(bank)
  }

  return (
    <div className="squad-pitch">
      <ImportTeam onImport={handleImportTeam} />

      {/*fpl bank figure  */}
      {importedBank !== null ? (
        <p className="budget-tracker">Bank: £{importedBank.toFixed(1)}m</p> // to fixed rounds to 1.dp 
      ) : (
        <p className={budgetRemaining < 0 ? 'budget-tracker over-budget' : 'budget-tracker'}>
          Budget remaining: £{budgetRemaining.toFixed(1)}m / £100.0m
        </p>
      )}

      <div className="pitch-layout">
        <div className="pitch-column">
          <PitchGrid
            squad={squad}
            onSlotClick={(position, index) => setOpenSlot({ position, index })}
          />
        </div>

        {openSlot && (
          <div className="picker-panel">
            <p>
              Picking a player for {openSlot.position} (slot {openSlot.index + 1})
            </p>

            <SlotRecommendation
              key={`${openSlot.position}-${openSlot.index}`}
              position={openSlot.position}
              otherPlayerIds={otherPlayerIdsForOpenSlot}
              onSelectPlayer={handleSelectPlayer}
            />

            <hr className="picker-divider" />

            <PlayerSelector
              players={players}
              position={openSlot.position}
              onSelectPlayer={handleSelectPlayer}
            />

            <button type="button" onClick={() => setOpenSlot(null)}>
              Close
            </button>
          </div>
        )}
      </div>

      <button type="button" onClick={handleScoreTeam}>
        Score My Team
      </button>

      <button type="button" onClick={handleGetRecommendations}>
        Get Recommendations
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

      <RecommendationsResult result={recommendationsResult} />
    </div>
  )
}

export default SquadPitch
