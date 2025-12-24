/**
 * @typedef {'count'|'freq'} WordMetric
 */

/**
 * @typedef {{ text: string, value: number }} WordItem
 */

/**
 * @typedef {{ category: string, metric: WordMetric, total_words: number, items: WordItem[] }} WordFreqResponse
 */

/**
 * Build the `/api/wordfreq` URL with query parameters.
 *
 * @param {{
 *   category: string,
 *   metric: WordMetric,
 *   top: number,
 *   minCount: number,
 *   refresh: boolean
 * }} params
 * @returns {string}
 */
export function buildWordfreqUrl({ category, metric, top, minCount, refresh }) {
  const searchParams = new URLSearchParams({
    category,
    metric,
    top: String(top),
    min_count: String(minCount),
    refresh: refresh ? 'true' : 'false'
  })

  return `/api/wordfreq?${searchParams.toString()}`
}

/**
 * Fetch word frequencies from the backend.
 *
 * @param {{
 *   category: string,
 *   metric: WordMetric,
 *   top: number,
 *   minCount: number,
 *   refresh: boolean
 * }} params
 * @returns {Promise<WordFreqResponse>}
 */
export async function fetchWordfreq(params) {
  const url = buildWordfreqUrl(params)
  const resp = await fetch(url)

  const body = await resp.json().catch(() => null)
  if (!resp.ok) {
    const detail = body?.detail ? String(body.detail) : `Request failed (${resp.status})`
    throw new Error(detail)
  }

  return body
}
