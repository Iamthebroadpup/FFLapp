import { useEffect, useState } from 'react'
import axios from 'axios'

interface Player {
  id: string
  name: string
  position: string
}

function App() {
  const [players, setPlayers] = useState<Player[]>([])
  const [playersLoading, setPlayersLoading] = useState(false)
  const [playersError, setPlayersError] = useState<string | null>(null)

  const fetchPlayers = () => {
    setPlayersLoading(true)
    setPlayersError(null)
    axios
      .get('/api/players')
      .then((resp) => setPlayers(resp.data))
      .catch((err) => {
        setPlayersError(err.message || 'Failed to load players')
      })
      .finally(() => setPlayersLoading(false))
  }

  useEffect(() => {
    fetchPlayers()
  }, [])

  return (
    <div>
      <h1>Fantasy Draft Assistant</h1>
      {playersLoading && <p>Loading players...</p>}
      {playersError && (
        <div>
          <p>Error: {playersError}</p>
          <button onClick={fetchPlayers}>Retry</button>
        </div>
      )}
      {!playersLoading && !playersError && (
        <ul>
          {players.map((p) => (
            <li key={p.id}>
              {p.name} - {p.position}
            </li>
          ))}
        </ul>
      )}
      <button onClick={fetchPlayers}>Refresh Players</button>
    </div>
  )
}

export default App
