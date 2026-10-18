import { expect, it } from 'vitest'
import { matchesSearch, manilaDate } from '@/utils/search'
it('matches keywords across fields regardless of order, accents and punctuation', () => {
  expect(matchesSearch('  JOSE   wifi ', ['WiFi problem', 'Jos\u00e9 Rivera'])).toBe(true)
  expect(matchesSearch('TCK 20261018 0001', ['TCK 20261018-0001'])).toBe(true)
  expect(matchesSearch('printer rivera', ['WiFi', 'Rivera'])).toBe(false)
  expect(matchesSearch('   ', [])).toBe(true)
})
it('uses Philippine calendar dates at midnight', () => {
  expect(manilaDate('2026-10-18T15:59:59Z')).toBe('2026-10-18')
  expect(manilaDate('2026-10-18T16:00:00Z')).toBe('2026-10-19')
})
