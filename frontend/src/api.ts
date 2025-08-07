export async function bootstrap(settings: any) {
  const r = await fetch('/api/bootstrap', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(settings)
  })
  if (!r.ok) throw new Error(await r.text())
  return r.json()
}

export async function getSuggestions(body: any) {
  const r = await fetch('/api/suggestions', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(body)
  })
  if (!r.ok) throw new Error(await r.text())
  return r.json()
}
