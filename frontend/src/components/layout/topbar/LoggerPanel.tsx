import { useState } from 'react'
import { Activity } from 'lucide-react'
import { Button } from '../../ui/Button'
import { LoggerModal } from '../../modals/LoggerModal'

export function LoggerPanel() {
  const [showLogger, setShowLogger] = useState(false)

  return (
    <>
      <Button
        variant="ghost"
        size="sm"
        onClick={() => setShowLogger(true)}
        className="w-9 px-0 relative"
        aria-label="Open activity logger"
      >
        <Activity className="w-4 h-4" />
        {/* Activity indicator badge */}
        <div className="absolute -top-1 -right-1 w-3 h-3 bg-green-500 rounded-full border border-background"></div>
      </Button>
      <LoggerModal open={showLogger} onOpenChange={setShowLogger} />
    </>
  )
}