import { useState, useEffect, useCallback } from 'react'

export function useFetch(fetchFn, deps = [], interval = null) {
  const [data, setData]       = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError]     = useState(null)

  const execute = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const result = await fetchFn()
      setData(result)
    } catch (err) {
      setError(err?.response?.data?.detail || err.message || 'An error occurred')
    } finally {
      setLoading(false)
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)

  useEffect(() => {
    execute()
  }, [execute])

  useEffect(() => {
    if (!interval) return
    const id = setInterval(execute, interval)
    return () => clearInterval(id)
  }, [execute, interval])

  return { data, loading, error, refetch: execute }
}
