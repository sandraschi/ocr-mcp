import React from 'react'
import { FileText, Settings, Info } from 'lucide-react'
import { cn } from '../../lib/utils'

interface RightSidebarProps {
  isOpen: boolean
}

export function RightSidebar({ isOpen }: RightSidebarProps) {
  return (
    <div
      className={cn(
        'fixed right-0 top-14 h-[calc(100vh-3.5rem)] w-80 bg-sidebar-background border-l border-sidebar-border transition-transform duration-300 ease-out z-40',
        isOpen ? 'translate-x-0' : 'translate-x-full'
      )}
    >
      <div className="p-4">
        <div className="space-y-4">
          {/* File Metadata */}
          <div className="glass rounded-lg p-4">
            <div className="flex items-center gap-2 mb-3">
              <FileText className="w-5 h-5" />
              <h3 className="font-medium">Document Info</h3>
            </div>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Status:</span>
                <span className="text-green-600">Ready</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Size:</span>
                <span>2.4 MB</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Pages:</span>
                <span>12</span>
              </div>
            </div>
          </div>

          {/* Processing Status */}
          <div className="glass rounded-lg p-4">
            <div className="flex items-center gap-2 mb-3">
              <Settings className="w-5 h-5" />
              <h3 className="font-medium">Processing Status</h3>
            </div>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">OCR Engine:</span>
                <span>Tesseract 5.3</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Quality:</span>
                <span>95.2%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Time:</span>
                <span>1.2s</span>
              </div>
            </div>
          </div>

          {/* System Info */}
          <div className="glass rounded-lg p-4">
            <div className="flex items-center gap-2 mb-3">
              <Info className="w-5 h-5" />
              <h3 className="font-medium">System Info</h3>
            </div>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Backends:</span>
                <span>3/5 Active</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Memory:</span>
                <span>256 MB</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Queue:</span>
                <span>0 jobs</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}