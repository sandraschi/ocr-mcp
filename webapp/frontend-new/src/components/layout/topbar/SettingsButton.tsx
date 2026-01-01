import React, { useState } from 'react'
import { Settings } from 'lucide-react'
import { Button } from '../../ui/Button'
import { SettingsModal } from '../../modals/SettingsModal'

export function SettingsButton() {
  const [showSettings, setShowSettings] = useState(false)

  return (
    <>
      <Button
        variant="ghost"
        size="sm"
        onClick={() => setShowSettings(true)}
        className="w-9 px-0"
        aria-label="Open settings"
      >
        <Settings className="w-4 h-4" />
      </Button>
      <SettingsModal open={showSettings} onOpenChange={setShowSettings} />
    </>
  )
}