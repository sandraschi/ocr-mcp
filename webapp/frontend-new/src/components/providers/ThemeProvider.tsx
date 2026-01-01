import React, { createContext, useContext, useEffect } from 'react'
import { useThemeStore } from '../../stores/themeStore'

const ThemeContext = createContext<ReturnType<typeof useThemeStore> | null>(null)

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const themeStore = useThemeStore()

  useEffect(() => {
    // Apply initial theme
    const resolvedMode = themeStore.resolvedMode
    document.documentElement.classList.toggle('dark', resolvedMode === 'dark')

    // Listen for system theme changes
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    const handleChange = (e: MediaQueryListEvent) => {
      if (themeStore.mode === 'system') {
        const newMode = e.matches ? 'dark' : 'light'
        themeStore.setMode('system') // This will recalculate resolvedMode
      }
    }

    mediaQuery.addEventListener('change', handleChange)
    return () => mediaQuery.removeEventListener('change', handleChange)
  }, [themeStore])

  return (
    <ThemeContext.Provider value={themeStore}>
      {children}
    </ThemeContext.Provider>
  )
}

export function useTheme() {
  const context = useContext(ThemeContext)
  if (!context) {
    throw new Error('useTheme must be used within ThemeProvider')
  }
  return context
}