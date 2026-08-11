// lets the user manually browse and pick a player for the given position,

function PlayerSelector({ players, position, onSelectPlayer }) {
  const eligiblePlayers = players
    .filter((player) => player.position === position)
    .sort((a, b) => b.now_cost - a.now_cost)

  return (
    <ul className="player-list">
      {eligiblePlayers.map((player) => (
        <li key={player.id}>
          <button type="button" onClick={() => onSelectPlayer(player)}>
            {player.first_name} {player.second_name} - £{player.now_cost}m
          </button>
        </li>
      ))}
    </ul>
  )
}

export default PlayerSelector
