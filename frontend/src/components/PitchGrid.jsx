import ShirtSlot from './ShirtSlot'

// how many slots to render for each position
const FORMATION = {
  GKP: 2,
  DEF: 5,
  MID: 5,
  FWD: 3,
}

// this just draws the grid of shirts and reports clicks back up via onSlotClick
function PitchGrid({ squad, onSlotClick }) {
  return (
    <>
      {Object.entries(FORMATION).map(([position, count]) => (

        // for each position create x shirt icons
        <div className="position-row" key={position}>
          {Array.from({ length: count }).map((_, index) => (

            <ShirtSlot
              key={`${position}-${index}`}
              position={position}
              player={squad[`${position}-${index}`]}
              onClick={() => onSlotClick(position, index)}
            />
          ))}

        </div>
      ))}
    </>
  )
}

export default PitchGrid
