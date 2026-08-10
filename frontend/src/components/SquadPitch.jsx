import { useState } from 'react'
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

  return (
    <div className="squad-pitch">
      {Object.entries(FORMATION).map(([position, count]) => (

        // for each position create x shirt icons
        <div className="position-row" key={position}>
          {Array.from({ length: count }).map((_, index) => (

            <ShirtSlot
              key={`${position}-${index}`}
              position={position}
              onClick={() => {
                const slot = { position, index }
                setOpenSlot(slot)
                console.log('clicked slot:', slot)
              }}
            />
          ))}

        </div>
      ))}
    </div>
  )
}

export default SquadPitch
