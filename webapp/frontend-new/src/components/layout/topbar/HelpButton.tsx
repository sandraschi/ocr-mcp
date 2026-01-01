import React, { useState } from 'react'
import { HelpCircle } from 'lucide-react'
import { Button } from '../../ui/Button'
import { HelpModal } from '../../modals/HelpModal'

export function HelpButton() {
  const [showHelp, setShowHelp] = useState(false)

  return (
    <>
      <Button
        variant="ghost"
        size="sm"
        onClick={() => setShowHelp(true)}
        className="w-9 px-0"
        aria-label="Open help"
      >
        <HelpCircle className="w-4 h-4" />
      </Button>
      <HelpModal open={showHelp} onOpenChange={setShowHelp} />
    </>
  )
}