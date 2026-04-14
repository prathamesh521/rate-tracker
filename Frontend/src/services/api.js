const BASE_URL = '/rates'

export async function getLatestRates(type = '') {
  const params = type ? `?type=${encodeURIComponent(type)}` : ''
  const res = await fetch(`${BASE_URL}/latest${params}`)
  if (!res.ok) throw new Error('Failed to fetch rates')
  return res.json()
}
