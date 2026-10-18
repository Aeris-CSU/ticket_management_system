import { expect, it } from 'vitest'
import { validMobileNumber } from '@/utils/phone'
it('accepts Philippine mobile formats and optional blank values', () => {
  for (const value of ['09171234567', '+639171234567', '+63 917 123 4567', '0917-123-4567', '']) expect(validMobileNumber(value)).toBe(true)
})
it('rejects letters, incorrect prefixes and incorrect lengths', () => {
  for (const value of ['hello123', '123', '08171234567', '091712345678', '+63917123456']) expect(validMobileNumber(value)).toBe(false)
})
