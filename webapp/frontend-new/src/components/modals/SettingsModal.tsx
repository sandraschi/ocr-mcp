import React, { useState } from 'react'
import { Settings, User, Palette, Bell, Shield, Monitor, Globe, Save, RotateCcw, Eye, EyeOff } from 'lucide-react'
import { Dialog, DialogHeader, DialogTitle, DialogClose, DialogContent, DialogFooter } from '../ui/Dialog'
import { Button } from '../ui/Button'
import { useThemeStore } from '../../stores/themeStore'
import { cn } from '../../lib/utils'

interface SettingsModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

type SettingsTab = 'general' | 'appearance' | 'notifications' | 'privacy' | 'system'

export function SettingsModal({ open, onOpenChange }: SettingsModalProps) {
  const [activeTab, setActiveTab] = useState<SettingsTab>('general')
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false)
  const { mode, setMode } = useThemeStore()

  // Mock settings state - in real app, this would come from a settings store
  const [settings, setSettings] = useState({
    general: {
      autoSave: true,
      keyboardShortcuts: true,
      showPreviews: true,
      defaultLanguage: 'auto',
      maxFileSize: 50
    },
    appearance: {
      theme: mode,
      fontSize: 'medium',
      reduceAnimations: false,
      highContrast: false
    },
    notifications: {
      processingComplete: true,
      batchUpdates: true,
      scannerStatus: true,
      systemHealth: false,
      notificationDuration: 5
    },
    privacy: {
      analytics: false,
      crashReporting: true,
      autoDeleteTemp: true,
      dataRetention: 30
    },
    system: {
      backendUrl: 'http://localhost:8000',
      enableDebug: false,
      logLevel: 'info',
      cacheSize: 100
    }
  })

  const tabs = [
    { id: 'general' as const, label: 'General', icon: Settings, color: 'text-blue-500' },
    { id: 'appearance' as const, label: 'Appearance', icon: Palette, color: 'text-purple-500' },
    { id: 'notifications' as const, label: 'Notifications', icon: Bell, color: 'text-green-500' },
    { id: 'privacy' as const, label: 'Privacy', icon: Shield, color: 'text-orange-500' },
    { id: 'system' as const, label: 'System', icon: Monitor, color: 'text-red-500' },
  ]

  const updateSetting = (category: keyof typeof settings, key: string, value: any) => {
    setSettings(prev => ({
      ...prev,
      [category]: {
        ...prev[category],
        [key]: value
      }
    }))
    setHasUnsavedChanges(true)
  }

  const handleSave = () => {
    // In real app, save to backend/localStorage
    console.log('Saving settings:', settings)

    // Update theme if changed
    if (settings.appearance.theme !== mode) {
      setMode(settings.appearance.theme)
    }

    setHasUnsavedChanges(false)
    onOpenChange(false)
  }

  const handleReset = () => {
    // Reset to defaults
    setSettings({
      general: {
        autoSave: true,
        keyboardShortcuts: true,
        showPreviews: true,
        defaultLanguage: 'auto',
        maxFileSize: 50
      },
      appearance: {
        theme: 'system',
        fontSize: 'medium',
        reduceAnimations: false,
        highContrast: false
      },
      notifications: {
        processingComplete: true,
        batchUpdates: true,
        scannerStatus: true,
        systemHealth: false,
        notificationDuration: 5
      },
      privacy: {
        analytics: false,
        crashReporting: true,
        autoDeleteTemp: true,
        dataRetention: 30
      },
      system: {
        backendUrl: 'http://localhost:8000',
        enableDebug: false,
        logLevel: 'info',
        cacheSize: 100
      }
    })
    setMode('system')
    setHasUnsavedChanges(true)
  }

  const renderGeneralSettings = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium mb-4 flex items-center gap-2">
          <Settings className="w-5 h-5" />
          General Preferences
        </h3>
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <label className="font-medium">Auto-save documents</label>
              <p className="text-sm text-muted-foreground">Automatically save processed documents</p>
            </div>
            <input
              type="checkbox"
              checked={settings.general.autoSave}
              onChange={(e) => updateSetting('general', 'autoSave', e.target.checked)}
              className="w-4 h-4"
            />
          </div>

          <div className="flex items-center justify-between">
            <div>
              <label className="font-medium">Enable keyboard shortcuts</label>
              <p className="text-sm text-muted-foreground">Use keyboard shortcuts for common actions</p>
            </div>
            <input
              type="checkbox"
              checked={settings.general.keyboardShortcuts}
              onChange={(e) => updateSetting('general', 'keyboardShortcuts', e.target.checked)}
              className="w-4 h-4"
            />
          </div>

          <div className="flex items-center justify-between">
            <div>
              <label className="font-medium">Show file previews</label>
              <p className="text-sm text-muted-foreground">Display thumbnails for uploaded files</p>
            </div>
            <input
              type="checkbox"
              checked={settings.general.showPreviews}
              onChange={(e) => updateSetting('general', 'showPreviews', e.target.checked)}
              className="w-4 h-4"
            />
          </div>

          <div>
            <label className="font-medium block mb-2">Default OCR Language</label>
            <select
              value={settings.general.defaultLanguage}
              onChange={(e) => updateSetting('general', 'defaultLanguage', e.target.value)}
              className="w-full px-3 py-2 bg-background border border-border rounded-md"
            >
              <option value="auto">Auto-detect</option>
              <option value="en">English</option>
              <option value="de">German</option>
              <option value="fr">French</option>
              <option value="es">Spanish</option>
            </select>
          </div>

          <div>
            <label className="font-medium block mb-2">Maximum file size (MB)</label>
            <input
              type="number"
              value={settings.general.maxFileSize}
              onChange={(e) => updateSetting('general', 'maxFileSize', Number(e.target.value))}
              min={1}
              max={500}
              className="w-full px-3 py-2 bg-background border border-border rounded-md"
            />
          </div>
        </div>
      </div>
    </div>
  )

  const renderAppearanceSettings = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium mb-4 flex items-center gap-2">
          <Palette className="w-5 h-5" />
          Appearance
        </h3>
        <div className="space-y-4">
          <div>
            <label className="font-medium block mb-3">Theme</label>
            <div className="grid grid-cols-3 gap-3">
              {[
                { value: 'light', label: 'Light', preview: 'bg-white border-gray-300' },
                { value: 'dark', label: 'Dark', preview: 'bg-gray-900 border-gray-700' },
                { value: 'system', label: 'System', preview: 'bg-gradient-to-r from-white to-gray-900 border-gray-400' }
              ].map((theme) => (
                <button
                  key={theme.value}
                  onClick={() => updateSetting('appearance', 'theme', theme.value)}
                  className={cn(
                    'p-3 border-2 rounded-lg text-center transition-all hover:scale-105',
                    settings.appearance.theme === theme.value
                      ? 'border-primary ring-2 ring-primary/20'
                      : 'border-border hover:border-primary/50'
                  )}
                >
                  <div className={cn('w-8 h-8 rounded mx-auto mb-2 border', theme.preview)}></div>
                  <div className="text-sm font-medium">{theme.label}</div>
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="font-medium block mb-2">Font Size</label>
            <select
              value={settings.appearance.fontSize}
              onChange={(e) => updateSetting('appearance', 'fontSize', e.target.value)}
              className="w-full px-3 py-2 bg-background border border-border rounded-md"
            >
              <option value="small">Small</option>
              <option value="medium">Medium</option>
              <option value="large">Large</option>
              <option value="extra-large">Extra Large</option>
            </select>
          </div>

          <div className="flex items-center justify-between">
            <div>
              <label className="font-medium">Reduce animations</label>
              <p className="text-sm text-muted-foreground">Minimize motion for accessibility</p>
            </div>
            <input
              type="checkbox"
              checked={settings.appearance.reduceAnimations}
              onChange={(e) => updateSetting('appearance', 'reduceAnimations', e.target.checked)}
              className="w-4 h-4"
            />
          </div>

          <div className="flex items-center justify-between">
            <div>
              <label className="font-medium">High contrast mode</label>
              <p className="text-sm text-muted-foreground">Increase contrast for better visibility</p>
            </div>
            <input
              type="checkbox"
              checked={settings.appearance.highContrast}
              onChange={(e) => updateSetting('appearance', 'highContrast', e.target.checked)}
              className="w-4 h-4"
            />
          </div>
        </div>
      </div>
    </div>
  )

  const renderNotificationSettings = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium mb-4 flex items-center gap-2">
          <Bell className="w-5 h-5" />
          Notifications
        </h3>
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <label className="font-medium">Processing completion</label>
              <p className="text-sm text-muted-foreground">Notify when OCR processing finishes</p>
            </div>
            <input
              type="checkbox"
              checked={settings.notifications.processingComplete}
              onChange={(e) => updateSetting('notifications', 'processingComplete', e.target.checked)}
              className="w-4 h-4"
            />
          </div>

          <div className="flex items-center justify-between">
            <div>
              <label className="font-medium">Batch processing updates</label>
              <p className="text-sm text-muted-foreground">Progress updates for batch operations</p>
            </div>
            <input
              type="checkbox"
              checked={settings.notifications.batchUpdates}
              onChange={(e) => updateSetting('notifications', 'batchUpdates', e.target.checked)}
              className="w-4 h-4"
            />
          </div>

          <div className="flex items-center justify-between">
            <div>
              <label className="font-medium">Scanner status changes</label>
              <p className="text-sm text-muted-foreground">Alerts for scanner connection issues</p>
            </div>
            <input
              type="checkbox"
              checked={settings.notifications.scannerStatus}
              onChange={(e) => updateSetting('notifications', 'scannerStatus', e.target.checked)}
              className="w-4 h-4"
            />
          </div>

          <div className="flex items-center justify-between">
            <div>
              <label className="font-medium">System health alerts</label>
              <p className="text-sm text-muted-foreground">Backend service status notifications</p>
            </div>
            <input
              type="checkbox"
              checked={settings.notifications.systemHealth}
              onChange={(e) => updateSetting('notifications', 'systemHealth', e.target.checked)}
              className="w-4 h-4"
            />
          </div>

          <div>
            <label className="font-medium block mb-2">Notification duration (seconds)</label>
            <input
              type="number"
              value={settings.notifications.notificationDuration}
              onChange={(e) => updateSetting('notifications', 'notificationDuration', Number(e.target.value))}
              min={1}
              max={30}
              className="w-full px-3 py-2 bg-background border border-border rounded-md"
            />
          </div>
        </div>
      </div>
    </div>
  )

  const renderPrivacySettings = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium mb-4 flex items-center gap-2">
          <Shield className="w-5 h-5" />
          Privacy & Security
        </h3>
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <label className="font-medium">Analytics collection</label>
              <p className="text-sm text-muted-foreground">Help improve the app with usage data</p>
            </div>
            <input
              type="checkbox"
              checked={settings.privacy.analytics}
              onChange={(e) => updateSetting('privacy', 'analytics', e.target.checked)}
              className="w-4 h-4"
            />
          </div>

          <div className="flex items-center justify-between">
            <div>
              <label className="font-medium">Crash reporting</label>
              <p className="text-sm text-muted-foreground">Automatically send crash reports</p>
            </div>
            <input
              type="checkbox"
              checked={settings.privacy.crashReporting}
              onChange={(e) => updateSetting('privacy', 'crashReporting', e.target.checked)}
              className="w-4 h-4"
            />
          </div>

          <div className="flex items-center justify-between">
            <div>
              <label className="font-medium">Auto-delete temp files</label>
              <p className="text-sm text-muted-foreground">Remove temporary files after processing</p>
            </div>
            <input
              type="checkbox"
              checked={settings.privacy.autoDeleteTemp}
              onChange={(e) => updateSetting('privacy', 'autoDeleteTemp', e.target.checked)}
              className="w-4 h-4"
            />
          </div>

          <div>
            <label className="font-medium block mb-2">Data retention (days)</label>
            <input
              type="number"
              value={settings.privacy.dataRetention}
              onChange={(e) => updateSetting('privacy', 'dataRetention', Number(e.target.value))}
              min={1}
              max={365}
              className="w-full px-3 py-2 bg-background border border-border rounded-md"
            />
          </div>

          <div className="pt-4 border-t border-border">
            <Button variant="outline" className="gap-2 w-full">
              <Eye className="w-4 h-4" />
              View Data & Privacy Policy
            </Button>
          </div>
        </div>
      </div>
    </div>
  )

  const renderSystemSettings = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium mb-4 flex items-center gap-2">
          <Monitor className="w-5 h-5" />
          System Configuration
        </h3>
        <div className="space-y-4">
          <div>
            <label className="font-medium block mb-2">Backend API URL</label>
            <input
              type="url"
              value={settings.system.backendUrl}
              onChange={(e) => updateSetting('system', 'backendUrl', e.target.value)}
              className="w-full px-3 py-2 bg-background border border-border rounded-md"
              placeholder="http://localhost:8000"
            />
          </div>

          <div className="flex items-center justify-between">
            <div>
              <label className="font-medium">Enable debug mode</label>
              <p className="text-sm text-muted-foreground">Show detailed debug information</p>
            </div>
            <input
              type="checkbox"
              checked={settings.system.enableDebug}
              onChange={(e) => updateSetting('system', 'enableDebug', e.target.checked)}
              className="w-4 h-4"
            />
          </div>

          <div>
            <label className="font-medium block mb-2">Log Level</label>
            <select
              value={settings.system.logLevel}
              onChange={(e) => updateSetting('system', 'logLevel', e.target.value)}
              className="w-full px-3 py-2 bg-background border border-border rounded-md"
            >
              <option value="error">Error</option>
              <option value="warn">Warning</option>
              <option value="info">Info</option>
              <option value="debug">Debug</option>
            </select>
          </div>

          <div>
            <label className="font-medium block mb-2">Cache Size (MB)</label>
            <input
              type="number"
              value={settings.system.cacheSize}
              onChange={(e) => updateSetting('system', 'cacheSize', Number(e.target.value))}
              min={10}
              max={1000}
              className="w-full px-3 py-2 bg-background border border-border rounded-md"
            />
          </div>

          <div className="pt-4 border-t border-border space-y-2">
            <Button variant="outline" size="sm" className="gap-2 w-full">
              <Globe className="w-4 h-4" />
              Check System Status
            </Button>
            <Button variant="outline" size="sm" className="gap-2 w-full">
              <RotateCcw className="w-4 h-4" />
              Clear System Cache
            </Button>
          </div>
        </div>
      </div>
    </div>
  )

  const renderTabContent = () => {
    switch (activeTab) {
      case 'general':
        return renderGeneralSettings()
      case 'appearance':
        return renderAppearanceSettings()
      case 'notifications':
        return renderNotificationSettings()
      case 'privacy':
        return renderPrivacySettings()
      case 'system':
        return renderSystemSettings()
      default:
        return renderGeneralSettings()
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange} className="w-[90vw] max-w-4xl h-[80vh]">
      <DialogHeader>
        <DialogTitle className="flex items-center gap-2">
          <Settings className="w-5 h-5" />
          Application Settings
        </DialogTitle>
        <DialogClose onClick={() => onOpenChange(false)} />
      </DialogHeader>

      <DialogContent className="flex h-full p-0">
        <div className="flex w-full h-full">
          {/* Sidebar */}
          <div className="w-48 border-r border-border p-4">
            <nav className="space-y-1">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={cn(
                    'w-full flex items-center gap-3 px-3 py-3 text-left rounded-lg transition-colors',
                    activeTab === tab.id
                      ? 'bg-primary text-primary-foreground'
                      : 'hover:bg-muted'
                  )}
                >
                  <tab.icon className={cn('w-5 h-5', activeTab === tab.id ? 'text-primary-foreground' : tab.color)} />
                  <span className="text-sm font-medium">{tab.label}</span>
                </button>
              ))}
            </nav>
          </div>

          {/* Content */}
          <div className="flex-1 p-6 overflow-y-auto">
            {renderTabContent()}
          </div>
        </div>
      </DialogContent>

      <DialogFooter>
        <div className="flex items-center justify-between w-full">
          <div className="text-sm text-muted-foreground">
            {hasUnsavedChanges && '⚠️ You have unsaved changes'}
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={handleReset}>
              <RotateCcw className="w-4 h-4 mr-2" />
              Reset
            </Button>
            <Button onClick={handleSave} disabled={!hasUnsavedChanges}>
              <Save className="w-4 h-4 mr-2" />
              Save Changes
            </Button>
          </div>
        </div>
      </DialogFooter>
    </Dialog>
  )
}