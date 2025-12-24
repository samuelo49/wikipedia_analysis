import { clamp, lerp } from './number.js'

/**
 * @typedef {{ text: string, value: number }} WordItem
 */

/**
 * Normalize word items and compute the min/max for scaling.
 *
 * @param {unknown} words
 * @returns {{ items: WordItem[], min: number, max: number }}
 */
export function normalizeWordItems(words) {
  const safeItems = Array.isArray(words) ? words : []
  const parsed = safeItems
    .map((w) => ({
      text: String(w?.text ?? ''),
      value: Number(w?.value ?? 0)
    }))
    .filter((w) => w.text && Number.isFinite(w.value) && w.value > 0)

  const values = parsed.map((w) => w.value)
  const min = values.length ? Math.min(...values) : 0
  const max = values.length ? Math.max(...values) : 1

  return { items: parsed, min, max }
}

/**
 * Convert word items into d3-cloud layout word objects.
 *
 * @param {WordItem[]} items
 * @param {{ min: number, max: number, minFont: number, maxFont: number }} scale
 * @returns {Array<{text: string, value: number, size: number}>}
 */
export function toLayoutWords(items, { min, max, minFont, maxFont }) {
  const denom = max - min
  return items.map((w) => {
    const t = denom > 0 ? (w.value - min) / denom : 1
    return {
      text: w.text,
      value: w.value,
      size: lerp(minFont, maxFont, clamp(t, 0, 1))
    }
  })
}
