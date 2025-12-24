import { useCallback, useMemo, useState } from 'react'
import { fetchWordfreq } from '../api/wordfreq.js'

/**
 * @typedef {'count'|'freq'} WordMetric
 */

/**
 * @typedef {{
 *  category: string,
 *  metric: WordMetric,
 *  top: number,
 *  minCount: number,
 *  refresh: boolean
 * }} WordfreqParams
 */

/**
 * Word frequency data loader.
 *
 * Encapsulates loading/error states and keeps the UI component focused on rendering.
 *
 * @param {WordfreqParams} params
 */
export function useWordfreq(params) {
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const stableParams = useMemo(
    () => ({
      category: params.category,
      metric: params.metric,
      top: params.top,
      minCount: params.minCount,
      refresh: params.refresh
    }),
    [params.category, params.metric, params.top, params.minCount, params.refresh]
  )

  const load = useCallback(async () => {
    setLoading(true)
    setError('')

    try {
      const resp = await fetchWordfreq(stableParams)
      setData(resp)
    } catch (e) {
      setData(null)
      setError(e?.message || String(e))
    } finally {
      setLoading(false)
    }
  }, [stableParams])

  return { data, error, loading, load }
}
