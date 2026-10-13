import { ref } from 'vue'

const THEME_STORAGE_KEY = 'tickarla-theme'

function savedDarkPreference() {
  if (typeof window === 'undefined') return false
  try {
    return window.localStorage.getItem(THEME_STORAGE_KEY) === 'dark'
  } catch {
    return false
  }
}

const isDark = ref(savedDarkPreference())

function applyTheme(dark: boolean) {
  if (typeof document !== 'undefined') {
    document.documentElement.dataset.theme = dark ? 'dark' : 'light'
    document.documentElement.style.colorScheme = dark ? 'dark' : 'light'
  }
  if (typeof window !== 'undefined') {
    try {
      window.localStorage.setItem(THEME_STORAGE_KEY, dark ? 'dark' : 'light')
    } catch {
      // The current page still changes theme when storage is unavailable.
    }
  }
}

export function initializeTheme() {
  applyTheme(isDark.value)
}

export function useTheme() {
  function toggleTheme() {
    isDark.value = !isDark.value
    applyTheme(isDark.value)
  }

  return { isDark, toggleTheme }
}
