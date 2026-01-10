import { useState, useRef, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { Languages, ChevronDown } from 'lucide-react'
import { Button } from '../../ui/Button'
import { cn } from '../../../lib/utils'

export function LanguageSelector() {
  const { i18n } = useTranslation()
  const [isOpen, setIsOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)
  const currentLang = i18n.language

  const languages = [
    { code: 'en', name: 'English' },
    { code: 'de', name: 'Deutsch' },
    { code: 'fr', name: 'Français' },
    { code: 'es', name: 'Español' }
  ]

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleLanguageChange = (langCode: string) => {
    i18n.changeLanguage(langCode)
    setIsOpen(false)
  }

  return (
    <div className="relative" ref={dropdownRef}>
      <Button
        variant="ghost"
        size="sm"
        className={cn(
          "h-9 px-3 flex items-center gap-2 transition-all duration-200",
          isOpen ? "bg-accent/50 text-accent-foreground" : "hover:bg-accent/30"
        )}
        onClick={() => setIsOpen(!isOpen)}
        aria-label="Select language"
      >
        <Languages className="w-4 h-4" />
        <span className="text-xs font-medium uppercase">{currentLang}</span>
        <ChevronDown className={cn("w-3 h-3 transition-transform duration-200", isOpen && "rotate-180")} />
      </Button>

      {isOpen && (
        <div className="absolute top-full right-0 mt-2 bg-background/60 backdrop-blur-xl border border-white/10 rounded-xl shadow-2xl py-1.5 min-w-[140px] z-50 animate-in fade-in slide-in-from-top-2 duration-200 overflow-hidden">
          <div className="px-3 py-1.5 text-[10px] font-semibold text-muted-foreground uppercase tracking-wider border-b border-white/5 mb-1">
            Language
          </div>
          {languages.map((lang) => (
            <button
              key={lang.code}
              onClick={() => handleLanguageChange(lang.code)}
              className={cn(
                "w-full text-left px-3 py-2 text-sm transition-all duration-200 flex items-center justify-between group",
                currentLang === lang.code
                  ? "bg-primary/20 text-primary font-medium"
                  : "hover:bg-white/10 text-muted-foreground hover:text-foreground"
              )}
            >
              <span>{lang.name}</span>
              {currentLang === lang.code && (
                <div className="w-1.5 h-1.5 rounded-full bg-primary shadow-[0_0_8px_rgba(var(--primary),0.8)]" />
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}