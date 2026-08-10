// Creates the shirt image - called an SVG 
// drawn out using vectors or smth  - can be filled in later using plain CSS
function ShirtSlot({ position, onClick }) {
  return (
    <button className="shirt-slot" type="button" onClick={onClick}>
      <svg viewBox="0 0 100 100" className="shirt-icon">
        <path d="M30,10 L40,10 Q50,20 60,10 L70,10 L90,30 L75,45 L70,40 L70,90 L30,90 L30,40 L25,45 L10,30 Z" />
      </svg>
      <span className="shirt-label">{position}</span>
    </button>
  )
}

export default ShirtSlot
