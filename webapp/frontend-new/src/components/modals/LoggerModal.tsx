import React, { useState, useEffect, useCallback } from 'react'
import { Activity, Download, Search, Filter, Trash2, AlertCircle, Info, CheckCircle, AlertTriangle } from 'lucide-react'
import { Dialog, DialogHeader, DialogTitle, DialogClose, DialogContent } from '../ui/Dialog'
import { Button } from '../ui/Button'
import { cn } from '../../lib/utils'

interface LogEntry {
  id: string
  timestamp: Date
  level: 'error' | 'warn' | 'info' | 'debug'
  source: string
  message: string
  details?: any
}

interface LoggerModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function LoggerModal({ open, onOpenChange }: LoggerModalProps) {
  const [logs, setLogs] = useState<LogEntry[]>([])
  const [filteredLogs, setFilteredLogs] = useState<LogEntry[]>([])
  const [searchTerm, setSearchTerm] = useState('')
  const [levelFilter, setLevelFilter] = useState<'all' | 'error' | 'warn' | 'info' | 'debug'>('all')
  const [autoScroll, setAutoScroll] = useState(true)

  // Mock log generation for demo
  useEffect(() => {
    if (!open) return

    const mockLogs: LogEntry[] = [
      {
        id: '1',
        timestamp: new Date(Date.now() - 300000),
        level: 'info',
        source: 'OCR-Engine',
        message: 'Document processing started',
        details: { fileId: 'doc-123', pages: 5 }
      },
      {
        id: '2',
        timestamp: new Date(Date.now() - 250000),
        level: 'info',
        source: 'Scanner',
        message: 'Scanner HP LaserJet connected',
        details: { deviceId: 'scanner-1', model: 'HP LaserJet MFP' }
      },
      {
        id: '3',
        timestamp: new Date(Date.now() - 200000),
        level: 'warn',
        source: 'Quality-Assessor',
        message: 'Document quality below threshold',
        details: { score: 65.2, threshold: 70.0 }
      },
      {
        id: '4',
        timestamp: new Date(Date.now() - 150000),
        level: 'error',
        source: 'Batch-Processor',
        message: 'File processing failed',
        details: { fileName: 'corrupted.pdf', error: 'Invalid PDF structure' }
      },
      {
        id: '5',
        timestamp: new Date(Date.now() - 100000),
        level: 'info',
        source: 'API',
        message: 'Batch processing completed',
        details: { processed: 12, failed: 1, totalTime: '45.2s' }
      },
      {
        id: '6',
        timestamp: new Date(Date.now() - 50000),
        level: 'debug',
        source: 'Memory-Manager',
        message: 'Cache cleared successfully',
        details: { freedMemory: '256MB', cacheSize: '0MB' }
      },
      {
        id: '7',
        timestamp: new Date(),
        level: 'info',
        source: 'System',
        message: 'Logger modal opened',
        details: { user: 'demo-user', sessionId: 'sess-123' }
      }
    ]

    setLogs(mockLogs)
  }, [open])

  // Filter logs based on search and level
  useEffect(() => {
    let filtered = logs

    // Apply level filter
    if (levelFilter !== 'all') {
      filtered = filtered.filter(log => log.level === levelFilter)
    }

    // Apply search filter
    if (searchTerm) {
      const term = searchTerm.toLowerCase()
      filtered = filtered.filter(log =>
        log.message.toLowerCase().includes(term) ||
        log.source.toLowerCase().includes(term) ||
        JSON.stringify(log.details).toLowerCase().includes(term)
      )
    }

    setFilteredLogs(filtered)
  }, [logs, searchTerm, levelFilter])

  const getLevelIcon = (level: LogEntry['level']) => {
    switch (level) {
      case 'error':
        return <AlertCircle className="w-4 h-4 text-red-500" />
      case 'warn':
        return <AlertTriangle className="w-4 h-4 text-yellow-500" />
      case 'info':
        return <Info className="w-4 h-4 text-blue-500" />
      case 'debug':
        return <Activity className="w-4 h-4 text-gray-500" />
      default:
        return <Info className="w-4 h-4 text-gray-500" />
    }
  }

  const getLevelColor = (level: LogEntry['level']) => {
    switch (level) {
      case 'error':
        return 'text-red-600 bg-red-50 dark:bg-red-950'
      case 'warn':
        return 'text-yellow-600 bg-yellow-50 dark:bg-yellow-950'
      case 'info':
        return 'text-blue-600 bg-blue-50 dark:bg-blue-950'
      case 'debug':
        return 'text-gray-600 bg-gray-50 dark:bg-gray-950'
      default:
        return 'text-gray-600 bg-gray-50 dark:bg-gray-950'
    }
  }

  const formatTimestamp = (timestamp: Date) => {
    return timestamp.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  }

  const handleExportLogs = useCallback(() => {
    const logData = filteredLogs.map(log => ({
      timestamp: log.timestamp.toISOString(),
      level: log.level.toUpperCase(),
      source: log.source,
      message: log.message,
      details: log.details
    }))

    const blob = new Blob([JSON.stringify(logData, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `ocr-logs-${new Date().toISOString().split('T')[0]}.json`
    a.click()
    URL.revokeObjectURL(url)
  }, [filteredLogs])

  const clearLogs = useCallback(() => {
    setLogs([])
    setFilteredLogs([])
  }, [])

  const levelCounts = {
    all: logs.length,
    error: logs.filter(l => l.level === 'error').length,
    warn: logs.filter(l => l.level === 'warn').length,
    info: logs.filter(l => l.level === 'info').length,
    debug: logs.filter(l => l.level === 'debug').length,
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange} className="w-[90vw] max-w-4xl h-[80vh]">
      <DialogHeader>
        <DialogTitle className="flex items-center gap-2">
          <Activity className="w-5 h-5" />
          Activity Logger
        </DialogTitle>
        <DialogClose onClick={() => onOpenChange(false)} />
      </DialogHeader>

      <DialogContent className="flex flex-col h-full">
        {/* Controls */}
        <div className="flex flex-col sm:flex-row gap-4 mb-4">
          {/* Search */}
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search logs..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>

          {/* Level Filters */}
          <div className="flex gap-1">
            {(['all', 'error', 'warn', 'info', 'debug'] as const).map((level) => (
              <button
                key={level}
                onClick={() => setLevelFilter(level)}
                className={cn(
                  'px-3 py-2 rounded-md text-xs font-medium transition-colors flex items-center gap-1',
                  levelFilter === level
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-muted hover:bg-muted/80'
                )}
              >
                {level !== 'all' && getLevelIcon(level)}
                <span className="capitalize">{level}</span>
                <span className="text-xs opacity-70">({levelCounts[level]})</span>
              </button>
            ))}
          </div>

          {/* Actions */}
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={handleExportLogs}>
              <Download className="w-4 h-4" />
              Export
            </Button>
            <Button variant="outline" size="sm" onClick={clearLogs}>
              <Trash2 className="w-4 h-4" />
              Clear
            </Button>
          </div>
        </div>

        {/* Log Entries */}
        <div className="flex-1 overflow-y-auto space-y-2">
          {filteredLogs.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <Activity className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>No logs found matching your criteria</p>
            </div>
          ) : (
            filteredLogs.map((log) => (
              <div
                key={log.id}
                className={cn(
                  'p-3 rounded-lg border transition-colors hover:bg-muted/50',
                  getLevelColor(log.level)
                )}
              >
                <div className="flex items-start gap-3">
                  {getLevelIcon(log.level)}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-sm font-medium text-muted-foreground">
                        {log.source}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        {formatTimestamp(log.timestamp)}
                      </span>
                      <span className={cn(
                        'px-2 py-0.5 rounded text-xs font-medium uppercase',
                        log.level === 'error' && 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
                        log.level === 'warn' && 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
                        log.level === 'info' && 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
                        log.level === 'debug' && 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200'
                      )}>
                        {log.level}
                      </span>
                    </div>
                    <p className="text-sm mb-1">{log.message}</p>
                    {log.details && (
                      <details className="text-xs">
                        <summary className="cursor-pointer text-muted-foreground hover:text-foreground">
                          Show details
                        </summary>
                        <pre className="mt-2 p-2 bg-muted rounded text-xs overflow-x-auto">
                          {JSON.stringify(log.details, null, 2)}
                        </pre>
                      </details>
                    )}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Footer Stats */}
        <div className="border-t border-border pt-4 mt-4">
          <div className="flex items-center justify-between text-sm text-muted-foreground">
            <span>Showing {filteredLogs.length} of {logs.length} entries</span>
            <div className="flex items-center gap-4">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={autoScroll}
                  onChange={(e) => setAutoScroll(e.target.checked)}
                  className="w-4 h-4"
                />
                Auto-scroll
              </label>
              <span>Real-time updates enabled</span>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}