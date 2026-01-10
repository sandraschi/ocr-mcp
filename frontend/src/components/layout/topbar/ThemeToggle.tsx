import { Moon, Sun } from 'lucide-react'
import { useThemeStore } from '../../../stores/themeStore'
import { Button } from '../../ui/Button'

export function ThemeToggle() {
  const { mode, setMode } = useThemeStore()

  const toggleTheme = () => {
    if (mode === 'light') {
      setMode('dark')
    } else if (mode === 'dark') {
      setMode('system')
    } else {
      setMode('light')
    }
  }

  const getIcon = () => {
    switch (mode) {
      case 'light':
        return <Sun className="w-4 h-4" />
      case 'dark':
        return <Moon className="w-4 h-4" />
      default:
        return <Sun className="w-4 h-4" />
    }
  }

  const getLabel = () => {
    switch (mode) {
      case 'light':
        return 'Light mode'
      case 'dark':
        return 'Dark mode'
      default:
        return 'System mode'
    }
  }

  return (
    <Button
      variant="ghost"
      size="sm"
      onClick={toggleTheme}
      className="w-9 px-0"
      aria-label={`Switch to ${mode === 'light' ? 'dark' : mode === 'dark' ? 'system' : 'light'} mode`}
    >
      {getIcon()}
      <span className="sr-only">{getLabel()}</span>
    </Button>
  )
}