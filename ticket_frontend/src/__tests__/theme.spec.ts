import { afterEach, describe, expect, it } from 'vitest'
import { mount, type VueWrapper } from '@vue/test-utils'
import ThemeToggle from '@/components/ThemeToggle.vue'

const wrappers: VueWrapper[] = []

afterEach(() => {
  wrappers.splice(0).forEach((wrapper) => wrapper.unmount())
  localStorage.removeItem('tickarla-theme')
  document.documentElement.dataset.theme = 'light'
})

describe('shared theme toggle', () => {
  it('persists the selected theme and synchronizes other toggles', async () => {
    localStorage.setItem('tickarla-theme', 'light')
    const landingToggle = mount(ThemeToggle)
    const dashboardToggle = mount(ThemeToggle)
    wrappers.push(landingToggle, dashboardToggle)

    expect(landingToggle.get('button').attributes('aria-label')).toBe('Switch to dark mode')
    await landingToggle.get('button').trigger('click')

    expect(document.documentElement.dataset.theme).toBe('dark')
    expect(localStorage.getItem('tickarla-theme')).toBe('dark')
    expect(dashboardToggle.get('button').attributes('aria-label')).toBe('Switch to light mode')

    await dashboardToggle.get('button').trigger('click')
    expect(document.documentElement.dataset.theme).toBe('light')
  })
})
