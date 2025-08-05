import { useEffect, useState } from 'react'
import { fetchPlayers, fetchInjuries, fetchProjections } from './api'

interface Player {
  id: string
  name: string
  position: string
}

interface Injury {
  id?: string
  name?: string
  status?: string
}

interface Projection {
  id?: string
  name?: string
  position?: string
  points?: number
}

function App() {
  const [players, setPlayers] = useState<Player[]>([])
  const [injuries, setInjuries] = useState<Injury[]>([])
  const [projections, setProjections] = useState<Projection[]>([])
  const [week, setWeek] = useState<number>(1)
  const [position, setPosition] = useState<string>('QB')

  useEffect(() => {
    fetchPlayers().then(setPlayers)
  }, [])

  useEffect(() => {
    fetchInjuries().then(setInjuries)
  }, [])

  useEffect(() => {
    fetchProjections(week, position).then(setProjections)
  }, [week, position])

  return (
    <div>
      <h1>Fantasy Draft Assistant</h1>
      <h2>Players</h2>
      <ul>
        {players.map((p) => (
          <li key={p.id}>{p.name} - {p.position}</li>
        ))}
      </ul>

      <h2>Injuries</h2>
      <ul>
        {injuries.map((i) => (
          <li key={i.id || i.name}>{i.name} - {i.status}</li>
        ))}
      </ul>

      <h2>Projections</h2>
      <div>
        <label>
          Week:
          <input type="number" min="1" value={week} onChange={(e) => setWeek(Number(e.target.value))} />
        </label>
        <label>
          Position:
          <select value={position} onChange={(e) => setPosition(e.target.value)}>
            <option value="QB">QB</option>
            <option value="RB">RB</option>
            <option value="WR">WR</option>
            <option value="TE">TE</option>
            <option value="K">K</option>
            <option value="DEF">DEF</option>
          </select>
        </label>
      </div>
      <table>
        <thead>
          <tr>
            <th>Player</th>
            <th>Position</th>
            <th>Points</th>
          </tr>
        </thead>
        <tbody>
          {projections.map((p) => (
            <tr key={p.id || p.name}>
              <td>{p.name}</td>
              <td>{p.position}</td>
              <td>{p.points}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default App
