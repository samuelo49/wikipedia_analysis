import { useEffect, useMemo, useState } from 'react'

import { useWordfreq } from './hooks/useWordfreq.js'
import WordCloud from './WordCloud.jsx'

const DEFAULT_CATEGORY = 'Large_language_models'

/**
 * Clamp a number between inclusive bounds.
 *
 * @param {number} value
 * @param {number} min
 * @param {number} max
 */
function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value))
}

export default function App() {
  const [category, setCategory] = useState(DEFAULT_CATEGORY)
  const [metric, setMetric] = useState('count')
  const [top, setTop] = useState(200)
  const [minCount, setMinCount] = useState(2)
  const [refresh, setRefresh] = useState(false)

  const params = useMemo(
    () => ({
      category,
      metric,
      top,
      minCount,
      refresh
    }),
    [category, metric, top, minCount, refresh]
  )

  const { data, error, loading, load } = useWordfreq(params)

  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const words = data?.items || []

  const maxWords = clamp(words.length, 0, 2000)

  return (
    <div className="page">
      <header className="header">
        <div className="title">Wikipedia Word Cloud</div>
        <div className="subtitle">
          Word size is proportional to {metric === 'freq' ? 'frequency' : 'count'}
        </div>
      </header>

      <section className="controls">
        <label className="field">
          <div className="label">Category</div>
          <input
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            placeholder="Large_language_models"
          />
        </label>

        <label className="field">
          <div className="label">Metric</div>
          <select value={metric} onChange={(e) => setMetric(e.target.value)}>
            <option value="count">count</option>
            <option value="freq">freq</option>
          </select>
        </label>

        <label className="field">
          <div className="label">Top N</div>
          <input
            type="number"
            min={10}
            max={2000}
            value={top}
            onChange={(e) => setTop(Number(e.target.value))}
          />
        </label>

        <label className="field">
          <div className="label">Min count</div>
          <input
            type="number"
            min={1}
            max={1000}
            value={minCount}
            onChange={(e) => setMinCount(Number(e.target.value))}
          />
        </label>

        <label className="check">
          <input
            type="checkbox"
            checked={refresh}
            onChange={(e) => setRefresh(e.target.checked)}
          />
          Force recompute (ignore cache)
        </label>

        <button className="btn" onClick={load} disabled={loading}>
          {loading ? 'Loading…' : 'Load'}
        </button>
      </section>

      {error ? (
        <div className="error">{error}</div>
      ) : null}

      <section className="meta">
        {data ? (
          <div>
            Category: <span className="mono">{data.category}</span> | Total words: <span className="mono">{data.total_words}</span> | Items: <span className="mono">{maxWords}</span>
          </div>
        ) : (
          <div>Enter a category and click Load.</div>
        )}
      </section>

      <main className="cloud">
        {words.length ? (
          <WordCloud words={words.slice(0, maxWords)} />
        ) : (
          <div className="empty">No data.</div>
        )}
      </main>
    </div>
  )
}
