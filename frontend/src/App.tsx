import { useEffect, useState } from 'react'
import axios from 'axios'

interface Player {
  id: string
  name: string
  position: string
}

function App() {
  const [players, setPlayers] = useState<Player[]>([])

  useEffect(() => {
    axios.get('/api/players').then((resp) => setPlayers(resp.data))
  }, [])

  return (
    <div>
      <h1>Fantasy Draft Assistant</h1>
      <ul>
        {players.map((p) => (
          <li key={p.id}>{p.name} - {p.position}</li>
        ))}
      </ul>
    </div>
  )
}

export default App
