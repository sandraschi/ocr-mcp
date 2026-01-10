import React, { useState } from 'react'
import { User, Palette, Bell, Shield, Settings as SettingsIcon, Save, RotateCcw } from 'lucide-react'
import { Button } from '../components/ui/Button'
import { cn } from '../lib/utils'
import { useThemeStore } from '../stores/themeStore'

type SettingsTab = 'general' | 'appearance' | 'notifications' | 'privacy'

export function SettingsPage() {
  const [activeTab, setActiveTab] = useState<SettingsTab>('general')
  const { mode, setMode } = useThemeStore()

  const tabs = [
    { id: 'general' as const, label: 'General', icon: SettingsIcon },
    { id: 'appearance' as const, label: 'Appearance', icon: Palette },
    { id: 'notifications' as const, label: 'Notifications', icon: Bell },
    { id: 'privacy' as const, label: 'Privacy', icon: Shield },
  ]

  const handleSaveSettings = () => {
    // TODO: Implement settings persistence
    console.log('Saving settings...')
  }

  const handleResetSettings = () => {
    // TODO: Implement settings reset
    console.log('Resetting settings...')
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Settings</h1>
        <p className="text-muted-foreground">
          Customize your OCR-MCP experience with comprehensive settings and preferences.
        </p>
      </div>

      <div className="glass rounded-lg overflow-hidden">
        <div className="flex border-b border-border">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={cn(
                'flex items-center gap-2 px-6 py-4 text-sm font-medium transition-colors flex-1 justify-center',
                activeTab === tab.id
                  ? 'bg-primary text-primary-foreground border-b-2 border-primary'
                  : 'hover:bg-accent text-muted-foreground hover:text-foreground'
              )}
            >
              <tab.icon className="w-4 h-4" />
              {tab.label}
            </button>
          ))}
        </div>

        <div className="p-6">
          {/* General Settings */}
          {activeTab === 'general' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-medium mb-4">General Preferences</h3>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <label className="font-medium">Auto-save documents</label>
                      <p className="text-sm text-muted-foreground">Automatically save processed documents</p>
                    </div>
                    <input type="checkbox" defaultChecked className="w-4 h-4" />
                  </div>

                  <div className="flex items-center justify-between">
                    <div>
                      <label className="font-medium">Enable keyboard shortcuts</label>
                      <p className="text-sm text-muted-foreground">Use keyboard shortcuts for common actions</p>
                    </div>
                    <input type="checkbox" defaultChecked className="w-4 h-4" />
                  </div>

                  <div className="flex items-center justify-between">
                    <div>
                      <label className="font-medium">Show file previews</label>
                      <p className="text-sm text-muted-foreground">Display thumbnails for uploaded files</p>
                    </div>
                    <input type="checkbox" defaultChecked className="w-4 h-4" />
                  </div>

                  <div>
                    <label className="font-medium block mb-2">Default OCR Language</label>
                    <select className="w-full px-3 py-2 bg-background border border-border rounded-md">
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
                      defaultValue={50}
                      min={1}
                      max={500}
                      className="w-full px-3 py-2 bg-background border border-border rounded-md"
                    />
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Appearance Settings */}
          {activeTab === 'appearance' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-medium mb-4">Appearance</h3>
                <div className="space-y-4">
                  <div>
                    <label className="font-medium block mb-2">Theme</label>
                    <div className="grid grid-cols-3 gap-3">
                      <button
                        onClick={() => setMode('light')}
                        className={cn(
                          'p-3 border-2 rounded-lg text-center transition-colors',
                          mode === 'light'
                            ? 'border-primary bg-primary/5'
                            : 'border-border hover:border-primary/50'
                        )}
                      >
                        <div className="w-8 h-8 bg-white border border-border rounded mx-auto mb-2"></div>
                        <div className="text-sm font-medium">Light</div>
                      </button>

                      <button
                        onClick={() => setMode('dark')}
                        className={cn(
                          'p-3 border-2 rounded-lg text-center transition-colors',
                          mode === 'dark'
                            ? 'border-primary bg-primary/5'
                            : 'border-border hover:border-primary/50'
                        )}
                      >
                        <div className="w-8 h-8 bg-gray-900 border border-border rounded mx-auto mb-2"></div>
                        <div className="text-sm font-medium">Dark</div>
                      </button>

                      <button
                        onClick={() => setMode('system')}
                        className={cn(
                          'p-3 border-2 rounded-lg text-center transition-colors',
                          mode === 'system'
                            ? 'border-primary bg-primary/5'
                            : 'border-border hover:border-primary/50'
                        )}
                      >
                        <div className="w-8 h-8 bg-gradient-to-r from-white to-gray-900 border border-border rounded mx-auto mb-2"></div>
                        <div className="text-sm font-medium">System</div>
                      </button>
                    </div>
                  </div>

                  <div>
                    <label className="font-medium block mb-2">Font Size</label>
                    <select className="w-full px-3 py-2 bg-background border border-border rounded-md">
                      <option value="small">Small</option>
                      <option value="medium" selected>Medium</option>
                      <option value="large">Large</option>
                      <option value="extra-large">Extra Large</option>
                    </select>
                  </div>

                  <div className="flex items-center justify-between">
                    <div>
                      <label className="font-medium">Reduce animations</label>
                      <p className="text-sm text-muted-foreground">Minimize motion for accessibility</p>
                    </div>
                    <input type="checkbox" className="w-4 h-4" />
                  </div>

                  <div className="flex items-center justify-between">
                    <div>
                      <label className="font-medium">High contrast mode</label>
                      <p className="text-sm text-muted-foreground">Increase contrast for better visibility</p>
                    </div>
                    <input type="checkbox" className="w-4 h-4" />
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Notifications Settings */}
          {activeTab === 'notifications' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-medium mb-4">Notifications</h3>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <label className="font-medium">Processing completion</label>
                      <p className="text-sm text-muted-foreground">Notify when OCR processing finishes</p>
                    </div>
                    <input type="checkbox" defaultChecked className="w-4 h-4" />
                  </div>

                  <div className="flex items-center justify-between">
                    <div>
                      <label className="font-medium">Batch processing updates</label>
                      <p className="text-sm text-muted-foreground">Progress updates for batch operations</p>
                    </div>
                    <input type="checkbox" defaultChecked className="w-4 h-4" />
                  </div>

                  <div className="flex items-center justify-between">
                    <div>
                      <label className="font-medium">Scanner status changes</label>
                      <p className="text-sm text-muted-foreground">Alerts for scanner connection issues</p>
                    </div>
                    <input type="checkbox" defaultChecked className="w-4 h-4" />
                  </div>

                  <div className="flex items-center justify-between">
                    <div>
                      <label className="font-medium">System health alerts</label>
                      <p className="text-sm text-muted-foreground">Backend service status notifications</p>
                    </div>
                    <input type="checkbox" className="w-4 h-4" />
                  </div>

                  <div>
                    <label className="font-medium block mb-2">Notification duration (seconds)</label>
                    <input
                      type="number"
                      defaultValue={5}
                      min={1}
                      max={30}
                      className="w-full px-3 py-2 bg-background border border-border rounded-md"
                    />
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Privacy Settings */}
          {activeTab === 'privacy' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-medium mb-4">Privacy & Security</h3>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <label className="font-medium">Analytics collection</label>
                      <p className="text-sm text-muted-foreground">Help improve the app with usage data</p>
                    </div>
                    <input type="checkbox" className="w-4 h-4" />
                  </div>

                  <div className="flex items-center justify-between">
                    <div>
                      <label className="font-medium">Crash reporting</label>
                      <p className="text-sm text-muted-foreground">Automatically send crash reports</p>
                    </div>
                    <input type="checkbox" defaultChecked className="w-4 h-4" />
                  </div>

                  <div className="flex items-center justify-between">
                    <div>
                      <label className="font-medium">Auto-delete temp files</label>
                      <p className="text-sm text-muted-foreground">Remove temporary files after processing</p>
                    </div>
                    <input type="checkbox" defaultChecked className="w-4 h-4" />
                  </div>

                  <div>
                    <label className="font-medium block mb-2">Data retention (days)</label>
                    <input
                      type="number"
                      defaultValue={30}
                      min={1}
                      max={365}
                      className="w-full px-3 py-2 bg-background border border-border rounded-md"
                    />
                  </div>

                  <div className="pt-4 border-t border-border">
                    <Button variant="outline" className="gap-2">
                      <Shield className="w-4 h-4" />
                      Clear All Data
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex justify-between items-center pt-6 border-t border-border">
            <Button variant="outline" onClick={handleResetSettings} className="gap-2">
              <RotateCcw className="w-4 h-4" />
              Reset to Defaults
            </Button>

            <Button onClick={handleSaveSettings} className="gap-2">
              <Save className="w-4 h-4" />
              Save Settings
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}