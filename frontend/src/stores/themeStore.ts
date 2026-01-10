import { create } from 'zustand'
import { persist } from 'zustand/middleware'

type ThemeMode = 'light' | 'dark' | 'system'

interface ThemeState {
  mode: ThemeMode
  resolvedMode: 'light' | 'dark'
  setMode: (mode: ThemeMode) => void
}

export const useThemeStore = create<ThemeState>()(
  persist(
    (set) => ({
      mode: 'system',
      resolvedMode: 'light',
      setMode: (mode) => {
        const resolvedMode = mode === 'system'
          ? (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light')
          : mode

        set({ mode, resolvedMode })

        // Apply theme to document
        document.documentElement.classList.toggle('dark', resolvedMode === 'dark')
      },
    }),
    {
      name: 'ocr-mcp-theme',
    }
  )
)

// Initialize theme on load
if (typeof window !== 'undefined') {
  const store = useThemeStore.getState()
  store.setMode(store.mode)
}