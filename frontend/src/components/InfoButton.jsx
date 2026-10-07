import { useState } from 'react'

function InfoButton() {
  const [open, setOpen] = useState(false)

  return (
    <>
      <button
        type="button"
        className="info-button"
        onClick={() => setOpen(true)}
        aria-label="How this page works"
      >
        i
      </button>

      {open && (
        <div className="info-overlay" onClick={() => setOpen(false)}>

          <div className="info-panel" onClick={(event) => event.stopPropagation()}>
            <h2>How this page works</h2>

            <p>
              Build a Fantasy Premier League squad here, or import your real one, and the
              app will tell you who to add and who to upgrade - based on its own scoring
              of every player in the league rather than opinion.
            </p>

            <h3>What the scores mean</h3>
            <p>
              Every player gets a score out of 100. It is <strong>relative to other players
              in the same position</strong>, not an absolute rating - the best goalkeeper in
              the league scores near 100 and the worst near 0, with everyone else spread
              between them. So a midfielder on 55 is not a bad player; they are mid-table
              on the things this algorithm measures.
            </p>

            <h3>What the algorithm looks at</h3>
            <p>
              Each position is judged on different things. Goalkeepers, for example, are
              scored on clean sheets (24%), value for money (22%), recent form (16%) and
              saves (9%), and marked down for goals conceded and hard upcoming fixtures.
            </p>
            <p>
              Value - points per million spent - carries a lot of weight in every position
              (17-22%). That is deliberate, and it is why a cheap player performing well can
              outrank an expensive one who isn't.
            </p>


            <h3>Squad rules</h3>
            <p>
              2 goalkeepers, 5 defenders, 5 midfielders and 3 forwards, within £100m, and no
              more than 3 players from any one club.
            </p>

            <h3>The assistant</h3>
            <p>
              The panel on the right answers questions in plain English - try "who should I
              bring in for midfield?" or "why is my score so low?". It works from the same
              scores and the same calculations the buttons use, so it cannot invent numbers.
            </p>

            <h3>How current is the data?</h3>
            <p>
              Player prices, points and form come from the official FPL API and refresh
              automatically whenever they are more than 12 hours old.
            </p>

            <button type="button" onClick={() => setOpen(false)}>
              Close
            </button>
          </div>
        </div>
      )}
    </>
  )
}

export default InfoButton
