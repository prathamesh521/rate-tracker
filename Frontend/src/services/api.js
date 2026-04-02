import axios from 'axios'

const client = axios.create({
  baseURL: '/rates',
  headers: { 'Content-Type': 'application/json' },
})

/**
 * Fetch the most recent rate for every (provider, type) combination.
 * @param {string} [type] - Optional rate type filter (case-insensitive)
 */
export async function getLatestRates(type = '') {
  const params = {}
  if (type) params.type = type
  const response = await client.get('/latest', { params })
  return response.data
}

/**
 * Fetch paginated rate history with optional filters.
 * @param {Object} filters
 * @param {string} [filters.provider]
 * @param {string} [filters.type]
 * @param {string} [filters.from]   - YYYY-MM-DD
 * @param {string} [filters.to]     - YYYY-MM-DD
 * @param {number} [filters.page]
 * @param {number} [filters.page_size]
 */
export async function getRateHistory(filters = {}) {
  const params = {}
  if (filters.provider) params.provider = filters.provider
  if (filters.type)     params.type     = filters.type
  if (filters.from)     params.from     = filters.from
  if (filters.to)       params.to       = filters.to
  if (filters.page)     params.page     = filters.page
  if (filters.page_size) params.page_size = filters.page_size
  const response = await client.get('/history', { params })
  return response.data
}
