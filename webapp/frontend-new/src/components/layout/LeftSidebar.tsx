import React from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { Upload, Layers, Printer, Search, BarChart3, Cog, Zap, FileText, Settings } from 'lucide-react'
import { cn } from '../../lib/utils'

interface LeftSidebarProps {
  isOpen: boolean
}

export function LeftSidebar({ isOpen }: LeftSidebarProps) {
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
        'fixed left-0 top-14 h-[calc(100vh-3.5rem)] w-64 bg-sidebar-background border-r border-sidebar-border transition-transform duration-300 ease-out z-40',
        isOpen ? 'translate-x-0' : '-translate-x-full'
      )}
    >
      <div className="p-4">
        <nav className="space-y-1">
          {menuItems.map((item) => {
            const isActive = location.pathname === item.path || (location.pathname === '/' && item.path === '/upload')
            return (
              <button
                key={item.id}
                onClick={() => handleMenuClick(item.path)}
                className={cn(
                  'w-full flex items-center gap-3 px-3 py-2 text-left rounded-md transition-colors hover:bg-sidebar-accent',
                  isActive
                    ? 'bg-sidebar-accent text-sidebar-accent-foreground font-medium'
                    : 'text-sidebar-foreground hover:text-sidebar-accent-foreground'
                )}
              >
                <item.icon className="w-5 h-5 flex-shrink-0" />
                <span className="text-sm">{item.label}</span>
              </button>
            )
          })}
        </nav>
      </div>
    </div>
  )
}