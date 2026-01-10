import { useNavigate, useLocation } from 'react-router-dom'
import { Upload, Layers, Printer, Search, BarChart3, Cog, Zap, FileText, Settings, Terminal } from 'lucide-react'
import { cn } from '../../lib/utils'


interface LeftSidebarProps {
  isOpen: boolean
  onOpenLogs?: () => void
}

export function LeftSidebar({ isOpen, onOpenLogs }: LeftSidebarProps) {
  const navigate = useNavigate()
  const location = useLocation()

  const menuItems = [
    { id: '/upload', label: 'Single Document', icon: Upload, path: '/upload' },
    { id: '/batch', label: 'Batch Processing', icon: Layers, path: '/batch' },
    { id: '/scanner', label: 'Scanner Control', icon: Printer, path: '/scanner' },
    { id: '/preprocessing', label: 'Image Preprocessing', icon: Zap, path: '/preprocessing' },
    { id: '/analysis', label: 'Document Analysis', icon: Search, path: '/analysis' },
    { id: '/quality', label: 'Quality Assessment', icon: BarChart3, path: '/quality' },
    { id: '/pipelines', label: 'Custom Pipelines', icon: Cog, path: '/pipelines' },
    { id: '/optimization', label: 'Auto-Optimization', icon: Zap, path: '/optimization' },
    { id: '/conversion', label: 'Format Conversion', icon: FileText, path: '/conversion' },
    { id: '/export', label: 'Export & Download', icon: FileText, path: '/export' },
    { id: '/settings', label: 'Settings', icon: Settings, path: '/settings' },
  ]

  const handleMenuClick = (path: string) => {
    navigate(path)
  }

  return (
    <div
      className={cn(
        'fixed left-0 top-14 h-[calc(100vh-3.5rem)] w-64 bg-sidebar-background border-r border-sidebar-border shadow-xl transition-transform duration-300 ease-out z-40 flex flex-col',
        isOpen ? 'translate-x-0' : '-translate-x-full'
      )}
    >
      <div className="flex-1 p-4 overflow-y-auto h-full min-h-0">
        <nav className="space-y-1">
          {menuItems.map((item) => {
            const isActive = location.pathname === item.path || (location.pathname === '/' && item.path === '/upload')
            return (
              <button
                key={item.id}
                onClick={() => handleMenuClick(item.path)}
                className={cn(
                  'w-full flex items-center gap-3 px-3 py-2 text-left rounded-md transition-all duration-200',
                  isActive
                    ? 'bg-primary/10 text-primary font-semibold shadow-sm ring-1 ring-primary/20'
                    : 'text-foreground/80 hover:bg-sidebar-accent hover:text-foreground'
                )}
              >
                <item.icon className="w-5 h-5 flex-shrink-0" />
                <span className="text-sm">{item.label}</span>
              </button>
            )
          })}
        </nav>
      </div>

      <div className="p-4 border-t border-sidebar-border/50 bg-sidebar-accent/5">
        <button
          onClick={onOpenLogs}
          className="w-full flex items-center gap-3 px-3 py-2 text-left rounded-md transition-all duration-300 hover:bg-primary/20 hover:text-primary group relative overflow-hidden"
        >
          <div className="absolute inset-0 bg-primary/5 opacity-0 group-hover:opacity-100 transition-opacity" />
          <Terminal className="w-5 h-5 flex-shrink-0 text-primary animate-pulse" />
          <div className="flex flex-col">
            <span className="text-sm font-semibold">System Console</span>
            <span className="text-[10px] uppercase tracking-tighter text-muted-foreground group-hover:text-primary/70">SOTA Monitoring</span>
          </div>
        </button>
      </div>
    </div>
  )
}
