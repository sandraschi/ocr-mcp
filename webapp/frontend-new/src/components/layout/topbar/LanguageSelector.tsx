import React from 'react'
import { useTranslation } from 'react-i18next'
import { Languages } from 'lucide-react'
import { Button } from '../../ui/Button'

export function LanguageSelector() {
  const { i18n } = useTranslation()
  const currentLang = i18n.language

  const languages = [
    { code: 'en', name: 'English' },
    { code: 'de', name: 'Deutsch' },
    { code: 'fr', name: 'Français' },
    { code: 'es', name: 'Español' }
  ]

  const handleLanguageChange = (langCode: string) => {
    i18n.changeLanguage(langCode)
  }

  return (
    <div className="relative">
      <Button
        variant="ghost"
        size="sm"
        className="w-9 px-0"
        aria-label="Select language"
        title={`Current language: ${currentLang.toUpperCase()}`}
      >
        <Languages className="w-4 h-4" />
      </Button>

      {/* Simple dropdown for now - could be enhanced with proper dropdown component */}
      <div className="absolute top-full right-0 mt-1 bg-card border border-border rounded-md shadow-lg py-1 min-w-32 z-50">
        {languages.map((lang) => (
          <button
            key={lang.code}
            onClick={() => handleLanguageChange(lang.code)}
            className={`w-full text-left px-3 py-2 text-sm hover:bg-accent transition-colors ${
              currentLang === lang.code ? 'bg-accent font-medium' : ''
            }`}
          >
            {lang.name}
          </button>
        ))}
      </div>
    </div>
  )
}