import axios from 'axios'

export const fetchPlayers = async () => {
  const resp = await axios.get('/api/players')
  return resp.data
}

export const fetchInjuries = async () => {
  const resp = await axios.get('/api/injuries')
  return resp.data
}

export const fetchProjections = async (week: number, position: string) => {
  const resp = await axios.get('/api/projections', { params: { week, position } })
  return resp.data
}
