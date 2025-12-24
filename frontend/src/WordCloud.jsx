import { useEffect, useMemo, useRef, useState } from 'react'
import cloud from 'd3-cloud'

import { normalizeWordItems, toLayoutWords } from './lib/words.js'

/**
 * SVG word cloud layout using `d3-cloud`.
 *
 * @param {{
 *  words: Array<{text: string, value: number}>,
 *  width?: number,
 *  height?: number,
 *  padding?: number
 * }} props
 */
export default function WordCloud({ words, width = 1000, height = 600, padding = 1 }) {
  const [layoutWords, setLayoutWords] = useState([])
  const [errorMessage, setErrorMessage] = useState('')
  const svgRef = useRef(null)

  const normalized = useMemo(() => normalizeWordItems(words), [words])

  useEffect(() => {
    let cancelled = false
    setErrorMessage('')

    if (!normalized.items.length) {
      setLayoutWords([])
      return () => {
        cancelled = true
      }
    }

    const minFontPx = 14
    const maxFontPx = 88

    const layoutInput = toLayoutWords(normalized.items, {
      min: normalized.min,
      max: normalized.max,
      minFont: minFontPx,
      maxFont: maxFontPx
    })

    const layout = cloud()
      .size([width, height])
      .words(layoutInput)
      .padding(padding)
      .rotate(() => (Math.random() < 0.18 ? 90 : 0))
      .font('ui-sans-serif, system-ui')
      .fontSize((d) => d.size)
      .on('end', (out) => {
        if (cancelled) return
        setLayoutWords(out)
      })

    try {
      layout.start()
    } catch (e) {
      if (cancelled) return
      setErrorMessage(e?.message || String(e))
      setLayoutWords([])
    }

    return () => {
      cancelled = true
      try {
        layout.stop()
      } catch {
        // ignore
      }
    }
  }, [normalized, width, height, padding])

  return (
    <div style={{ width: '100%', height: '100%', position: 'relative' }}>
      {errorMessage ? <div className="error">{errorMessage}</div> : null}
      <svg
        ref={svgRef}
        width="100%"
        height="100%"
        viewBox={`0 0 ${width} ${height}`}
        preserveAspectRatio="xMidYMid meet"
      >
        <g transform={`translate(${width / 2}, ${height / 2})`}>
          {layoutWords.map((w, i) => (
            <text
              key={`${w.text}-${i}`}
              textAnchor="middle"
              transform={`translate(${w.x}, ${w.y}) rotate(${w.rotate})`}
              style={{
                fontSize: `${w.size}px`,
                fontFamily: w.font || 'ui-sans-serif, system-ui',
                fill: 'rgba(255,255,255,0.92)'
              }}
            >
              {w.text}
            </text>
          ))}
        </g>
      </svg>
    </div>
  )
}
