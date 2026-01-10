import { AuthControls } from './topbar/AuthControls'
import { ThemeToggle } from './topbar/ThemeToggle'
import { LanguageSelector } from './topbar/LanguageSelector'
import { HelpButton } from './topbar/HelpButton'
import { LoggerPanel } from './topbar/LoggerPanel'
import { SettingsButton } from './topbar/SettingsButton'
import { useLayoutStore } from '../../stores/layoutStore'

export function Topbar() {
  const { toggleLeftSidebar } = useLayoutStore()

  return (
    <div className="h-14 glass border-b border-border/50 flex items-center justify-between px-4 sticky top-0 z-50">
      {/* Left side - Navigation */}
      <div className="flex items-center gap-4">
        <button
          onClick={toggleLeftSidebar}
          className="p-2 hover:bg-accent rounded-md transition-colors"
          aria-label="Toggle navigation menu"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>

        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
            <span className="text-primary-foreground font-bold text-sm">OCR</span>
          </div>
          <span className="font-semibold text-lg">OCR-MCP</span>
        </div>
      </div>

      {/* Center - Status */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
          <span>System Ready</span>
        </div>
      </div>

      {/* Right side - Controls */}
      <div className="flex items-center gap-2">
        <LoggerPanel />
        <HelpButton />
        <SettingsButton />
        <LanguageSelector />
        <ThemeToggle />
        <AuthControls />
      </div>
    </div>
  )
}