export const mobileNumberMessage = 'Enter a Philippine mobile number such as 09171234567 or +639171234567.'
export function validMobileNumber(value: string): boolean {
  if (!value.trim()) return true
  return /^(?:09[0-9]{9}|\+639[0-9]{9})$/.test(value.trim().replace(/[\s-]/g, ''))
}
