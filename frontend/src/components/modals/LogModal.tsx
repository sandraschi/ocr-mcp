import { useState, useEffect } from 'react'
import { Terminal, Trash2, Download, Maximize2, Minimize2, X } from 'lucide-react'
import { cn } from '../../lib/utils'
import { Button } from '../ui/Button'
import { Dialog, DialogContent } from '../ui/Dialog'

interface LogEntry {
    id: string
    timestamp: string
    level: 'info' | 'warn' | 'error' | 'success'
    module: string
    message: string
}

interface LogModalProps {
    open: boolean
    onOpenChange: (open: boolean) => void
}

export function LogModal({ open, onOpenChange }: LogModalProps) {
    const [logs, setLogs] = useState<LogEntry[]>([])
    const [isMaximized, setIsMaximized] = useState(false)

    // Mock initial logs
    useEffect(() => {
        if (open && logs.length === 0) {
            setLogs([
                { id: '1', timestamp: new Date().toISOString(), level: 'info', module: 'System', message: 'OCR-MCP Core Initialized SOTA Protocol' },
                { id: '2', timestamp: new Date().toISOString(), level: 'success', module: 'Backend', message: 'Connected to vision-mcp-server :: Ready for inference' },
                { id: '3', timestamp: new Date().toISOString(), level: 'info', module: 'UI', message: 'Glassmorphic styles applied successfully' },
                { id: '4', timestamp: new Date(Date.now() - 1000 * 60).toISOString(), level: 'warn', module: 'Scanner', message: 'WIA interface latency detected > 50ms' },
                { id: '5', timestamp: new Date(Date.now() - 1000 * 120).toISOString(), level: 'info', module: 'Cache', message: 'Prefetching transformer weights for Qwen2-VL' },
            ])
        }
    }, [open, logs.length])

    if (!open) return null

    const clearLogs = () => setLogs([])

    const getLevelColor = (level: string) => {
        switch (level) {
            case 'success': return 'text-emerald-400'
            case 'error': return 'text-rose-400'
            case 'warn': return 'text-amber-400'
            default: return 'text-sky-400'
        }
    }

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className={cn(
                "p-0 overflow-hidden transition-all duration-300 shadow-2xl",
                isMaximized
                    ? "fixed inset-0 w-screen h-screen max-w-none rounded-none border-0"
                    : "w-[90vw] max-w-4xl h-[70vh] rounded-xl border border-border"
            )}>
                {/* Header */}
                <div className="flex items-center justify-between px-6 py-4 border-b border-border bg-muted">
                    <div className="flex items-center gap-3">
                        <div className="p-2 rounded-lg bg-primary/20 text-primary">
                            <Terminal className="w-5 h-5" />
                        </div>
                        <div>
                            <h2 className="text-lg font-bold tracking-tight">System Console</h2>
                            <div className="flex items-center gap-2">
                                <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                                <span className="text-[10px] uppercase tracking-widest text-muted-foreground font-semibold">Live Monitoring SOTA</span>
                            </div>
                        </div>
                    </div>

                    <div className="flex items-center gap-2">
                        <Button variant="ghost" size="sm" className="h-8 px-2" onClick={() => setIsMaximized(!isMaximized)}>
                            {isMaximized ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
                        </Button>
                        <Button variant="ghost" size="sm" className="h-8 px-2 text-rose-400 hover:text-rose-300 hover:bg-rose-400/10" onClick={clearLogs}>
                            <Trash2 className="w-4 h-4" />
                        </Button>
                        <Button variant="ghost" size="sm" className="h-8 px-2" onClick={() => onOpenChange(false)}>
                            <X className="w-5 h-5" />
                        </Button>
                    </div>
                </div>

                {/* Log Content */}
                <div className="flex-1 overflow-auto p-6 font-mono text-xs sm:text-sm selection:bg-primary/30 h-[calc(100%-88px)]">
                    <div className="space-y-1.5">
                        {logs.length === 0 ? (
                            <div className="h-full flex flex-col items-center justify-center opacity-30 py-32">
                                <Terminal className="w-12 h-12 mb-4" />
                                <p>Console clear. Awaiting input...</p>
                            </div>
                        ) : (
                            logs.map((log) => (
                                <div key={log.id} className="group flex gap-4 hover:bg-white/5 p-1 rounded transition-colors border-l-2 border-transparent hover:border-primary/50">
                                    <span className="text-muted-foreground whitespace-nowrap opacity-50 w-24">
                                        [{new Date(log.timestamp).toLocaleTimeString()}]
                                    </span>
                                    <span className={cn("font-bold min-w-[80px]", getLevelColor(log.level))}>
                                        {log.level.toUpperCase()}
                                    </span>
                                    <span className="text-primary/70 font-semibold min-w-[100px]">
                                        {log.module}
                                    </span>
                                    <span className="text-foreground/90 leading-relaxed">
                                        {log.message}
                                    </span>
                                </div>
                            ))
                        )}
                        <div className="h-4" />
                    </div>
                </div>

                {/* Footer */}
                <div className="px-6 py-3 border-t border-white/10 bg-black/40 flex items-center justify-between text-[10px] uppercase tracking-wider font-semibold text-muted-foreground">
                    <div className="flex gap-4">
                        <span>Total Entries: {logs.length}</span>
                        <span>Buffer: 1024/2048 KB</span>
                    </div>
                    <button className="flex items-center gap-1.5 hover:text-foreground transition-colors">
                        <Download className="w-3 h-3" />
                        Export Session
                    </button>
                </div>
            </DialogContent>
        </Dialog>
    )
}
