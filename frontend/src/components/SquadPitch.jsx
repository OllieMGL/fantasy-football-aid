import { useState, useEffect } from 'react'
import PitchGrid from './PitchGrid'
import PlayerSelector from './PlayerSelector'
import SlotRecommendation from './SlotRecommendation'
import RecommendationsResult from './RecommendationsResult'
import ImportTeam from './ImportTeam'
import AskAI from './AskAI'
import InfoButton from './InfoButton'


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

  // recommendations score the whole league, so it takes a moment - without this
  // the button looks like it did nothing
  const [recommendationsLoading, setRecommendationsLoading] = useState(false)

  // 100m for a squad built by hand. Importing a team changes it to that squad's
  // value + its bank - see handleImportTeam. Sent to the backend with every
  // request that needs it, so the whole app uses the same number
  const [budget, setBudget] = useState(100)

  const [serverError, setServerError] = useState(null)

  useEffect(() => {
    fetch('http://127.0.0.1:5000/players')
      .then((response) => response.json())
      .then((data) => setPlayers(data))
      // fetch only rejects on a network failure, so this is the "backend isn't
      // running" case rather than an error response from it
      .catch(() => setServerError("Can't reach the server"))
  }, [])

  const amountSpent = Object.values(squad)
    .filter(Boolean)
    // .reduce takes the array down to one value ==> total money spent
    .reduce((total, player) => total + player.now_cost, 0) // inital value is 0

  // rounded to 1 d.p. - adding up prices like 5.1 + 4.3 gives tiny float errors,
  // which could show as "-0.0" and turn the tracker red for no reason
  const budgetRemaining = Math.round((budget - amountSpent) * 10) / 10

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
      .catch(() => setScoreResult({ error: "Can't reach the server" }))
  }

  function handleGetRecommendations() {
    setRecommendationsLoading(true)

    fetch('http://127.0.0.1:5000/recommendations', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ player_ids: getPlayerIds(), budget }),
    })
      .then((response) => response.json())
      .then((data) => {
        setRecommendationsResult(data)
        setRecommendationsLoading(false)
      })
      .catch(() => {
        setRecommendationsResult({ error: "Can't reach the server" })
        setRecommendationsLoading(false) 
      })
  }

  // applies the transfers ai suggested, players already checked in the backend 
  function handleApplyChanges(changes) {
    let newPlayerIds = getPlayerIds()

    for (const change of changes) {
      // out_id is null when the AI is filling an empty slot - nobody to remove
      if (change.out_id !== null) {
        newPlayerIds = newPlayerIds.filter((id) => id !== change.out_id)
      }

      newPlayerIds.push(change.in_id)
    }

    // rebuilds the pitch from a list of ids
    setSquad(buildSquadFromPlayerIds(newPlayerIds, players))
  }

  function handleImportTeam(playerIds, bank) {
    setSquad(buildSquadFromPlayerIds(playerIds, players))

    // an imported team's budget is what its players are worth today + the money
    // in the bank - so it starts with exactly the bank left to spend
    let squadValue = 0
    for (const id of playerIds) {
      const player = players.find((candidate) => candidate.id === id)
      squadValue += player.now_cost
    }

    setBudget(Math.round((squadValue + bank) * 10) / 10)
  }

  return (
    <div className="squad-pitch">
      
      <div className="page-header">
        {/* toFixed(1) shows 1 d.p. */}
        <p className={budgetRemaining < 0 ? 'budget-tracker over-budget' : 'budget-tracker'}>
          Budget remaining: £{budgetRemaining.toFixed(1)}m / £{budget.toFixed(1)}m
        </p>

        <InfoButton />
      </div>

      {serverError && <p className="server-error">{serverError}</p>}

      <div className="pitch-layout">
        <div className="pitch-column">
          <PitchGrid
            squad={squad}
            onSlotClick={(position, index) => setOpenSlot({ position, index })}
          />

          <div className="action-buttons-row">
            <button type="button" onClick={handleScoreTeam} className="primary-button-sm">
              Score My Team
            </button>

            <button
              type="button"
              onClick={handleGetRecommendations}
              disabled={recommendationsLoading}
              className="primary-button-sm"
            >
              {recommendationsLoading ? 'Working...' : 'Get Recommendations'}
            </button>
          </div>

          <ImportTeam onImport={handleImportTeam} />
        </div>

        <div className="side-column">
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

          <RecommendationsResult
            result={recommendationsResult}
            onClose={() => setRecommendationsResult(null)}
          />

          {openSlot && (
            <div className="picker-panel">
              <p>
                Picking a player for {openSlot.position} (slot {openSlot.index + 1})
              </p>

              <SlotRecommendation
                key={`${openSlot.position}-${openSlot.index}`}
                position={openSlot.position}
                otherPlayerIds={otherPlayerIdsForOpenSlot}
                budget={budget}
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
      </div>

      <AskAI playerIds={getPlayerIds()} budget={budget} onApplyChanges={handleApplyChanges} />
    </div>
  )
}

export default SquadPitch
