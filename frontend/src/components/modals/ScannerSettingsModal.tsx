import { useState, useEffect } from 'react'
import { Settings, Printer, Save, TestTube, RotateCcw, Eye, Target, Zap, Loader2, AlertCircle } from 'lucide-react'
import { Dialog, DialogHeader, DialogTitle, DialogClose, DialogContent, DialogFooter } from '../ui/Dialog'
import { Button } from '../ui/Button'
import { cn } from '../../lib/utils'
import { apiService, Scanner } from '../../services/api'

interface ScannerSettingsModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

interface ScanProfile {
  id: string
  name: string
  description: string
  settings: {
    dpi: number
    colorMode: string
    paperSize: string
    brightness: number
    contrast: number
    gamma: number
  }
}

export function ScannerSettingsModal({ open, onOpenChange }: ScannerSettingsModalProps) {
  const [scanners, setScanners] = useState<Scanner[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selectedScanner, setSelectedScanner] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'device' | 'profiles' | 'advanced' | 'calibration'>('device')
  const [scanSettings, setScanSettings] = useState({
    dpi: 300,
    colorMode: 'Grayscale',
    paperSize: 'A4',
    brightness: 0,
    contrast: 0,
    gamma: 1.0
  })

  const fetchScanners = async () => {
    setIsLoading(true)
    setError(null)
    try {
      const data = await apiService.getScanners()
      setScanners(data.scanners)
      if (data.scanners.length > 0 && !selectedScanner) {
        setSelectedScanner(data.scanners[0].id)
      }
    } catch (err) {
      console.error('Failed to fetch scanners:', err)
      setError('Failed to discover scanners. Make sure the scanner bridge is running on your host.')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    if (open) {
      fetchScanners()
    }
  }, [open])

  const scanProfiles: ScanProfile[] = [
    {
      id: 'document',
      name: 'Document',
      description: 'High-quality scanning for text documents',
      settings: { dpi: 300, colorMode: 'Grayscale', paperSize: 'A4', brightness: 0, contrast: 0, gamma: 1.0 }
    },
    {
      id: 'photo',
      name: 'Photo',
      description: 'High-resolution color scanning for photographs',
      settings: { dpi: 600, colorMode: 'Color', paperSize: 'A4', brightness: 5, contrast: 10, gamma: 1.2 }
    },
    {
      id: 'ocr',
      name: 'OCR Optimized',
      description: 'Optimized settings for best OCR accuracy',
      settings: { dpi: 400, colorMode: 'Grayscale', paperSize: 'A4', brightness: -5, contrast: 15, gamma: 1.0 }
    },
    {
      id: 'archive',
      name: 'Archive',
      description: 'Maximum quality for long-term storage',
      settings: { dpi: 600, colorMode: 'Color', paperSize: 'A4', brightness: 0, contrast: 0, gamma: 1.0 }
    }
  ]

  const [customProfiles] = useState<ScanProfile[]>([])
  const [selectedProfile, setSelectedProfile] = useState<string>('document')

  const tabs = [
    { id: 'device' as const, label: 'Device', icon: Printer },
    { id: 'profiles' as const, label: 'Profiles', icon: Target },
    { id: 'advanced' as const, label: 'Advanced', icon: Settings },
    { id: 'calibration' as const, label: 'Calibration', icon: TestTube },
  ]

  const handleSaveSettings = () => {
    console.log('Saving scanner settings:', { selectedScanner, scanSettings })
    onOpenChange(false)
  }

  const handleTestScan = () => {
    console.log('Running test scan with settings:', scanSettings)
  }

  const handleApplyProfile = (profileId: string) => {
    const profile = [...scanProfiles, ...customProfiles].find(p => p.id === profileId)
    if (profile) {
      setScanSettings(profile.settings)
      setSelectedProfile(profileId)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'connected':
        return 'text-green-600 bg-green-50 dark:bg-green-950'
      case 'disconnected':
        return 'text-gray-600 bg-gray-50 dark:bg-gray-950'
      case 'error':
        return 'text-red-600 bg-red-50 dark:bg-red-950'
      default:
        return 'text-gray-600 bg-gray-50 dark:bg-gray-950'
    }
  }

  const renderDeviceTab = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium mb-4">Scanner Selection</h3>

        {isLoading && (
          <div className="flex flex-col items-center justify-center p-12 border border-dashed rounded-lg bg-muted/50">
            <Loader2 className="w-8 h-8 text-primary animate-spin mb-4" />
            <p className="text-sm text-muted-foreground text-center">
              Discovering scanner devices... This may take a few seconds as we poll your local connection.
            </p>
          </div>
        )}

        {error && (
          <div className="p-4 border border-red-200 bg-red-50 dark:bg-red-950/20 dark:border-red-900/50 rounded-lg flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-600 mt-0.5" />
            <div className="space-y-1">
              <h4 className="text-sm font-medium text-red-800 dark:text-red-400">Discovery Error</h4>
              <p className="text-sm text-red-700 dark:text-red-500">{error}</p>
              <Button
                variant="ghost"
                size="sm"
                className="text-red-700 dark:text-red-400 hover:bg-red-100 dark:hover:bg-red-900/40 p-0 h-auto"
                onClick={fetchScanners}
              >
                Try Again
              </Button>
            </div>
          </div>
        )}

        {!isLoading && !error && scanners.length === 0 && (
          <div className="flex flex-col items-center justify-center p-12 border border-dashed rounded-lg bg-muted/50">
            <Printer className="w-8 h-8 text-muted-foreground mb-4" />
            <p className="text-sm text-muted-foreground text-center mb-2">
              No scanners found.
            </p>
            <p className="text-xs text-muted-foreground text-center max-w-sm">
              Please ensure your scanner is connected and the scanner bridge is running on the host machine.
            </p>
            <Button variant="outline" size="sm" className="mt-4" onClick={fetchScanners}>
              Rescan for Devices
            </Button>
          </div>
        )}

        <div className="space-y-3">
          {!isLoading && scanners.map((scanner) => (
            <div
              key={scanner.id}
              className={cn(
                'p-4 border rounded-lg cursor-pointer transition-all',
                selectedScanner === scanner.id
                  ? 'border-primary bg-primary/5'
                  : 'border-border hover:border-primary/50'
              )}
              onClick={() => setSelectedScanner(scanner.id)}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Printer className="w-6 h-6 text-primary" />
                  <div>
                    <h4 className="font-medium">{scanner.name}</h4>
                    <p className="text-sm text-muted-foreground">
                      {scanner.manufacturer || 'WIA Device'} • {scanner.type}
                    </p>
                  </div>
                </div>
                <div className={cn('px-3 py-1 rounded-full text-xs font-medium', getStatusColor(scanner.status))}>
                  {scanner.status}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="pt-4 border-t border-border">
        <Button
          variant="outline"
          className="gap-2"
          onClick={fetchScanners}
          disabled={isLoading}
        >
          <RotateCcw className={cn("w-4 h-4", isLoading && "animate-spin")} />
          Refresh Device List
        </Button>
      </div>
    </div>
  )

  const renderProfilesTab = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium mb-4">Scan Profiles</h3>
        <p className="text-muted-foreground mb-4">
          Choose from predefined profiles or create custom ones for different scanning needs.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[...scanProfiles, ...customProfiles].map((profile) => (
            <div
              key={profile.id}
              className={cn(
                'p-4 border rounded-lg cursor-pointer transition-all',
                selectedProfile === profile.id
                  ? 'border-primary bg-primary/5'
                  : 'border-border hover:border-primary/50'
              )}
              onClick={() => handleApplyProfile(profile.id)}
            >
              <div className="flex items-center gap-3 mb-2">
                <Target className="w-5 h-5 text-primary" />
                <h4 className="font-medium">{profile.name}</h4>
              </div>
              <p className="text-sm text-muted-foreground mb-3">{profile.description}</p>
              <div className="text-xs text-muted-foreground space-y-1">
                <div>{profile.settings.dpi} DPI • {profile.settings.colorMode}</div>
                <div>{profile.settings.paperSize} • B:{profile.settings.brightness} C:{profile.settings.contrast}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="pt-4 border-t border-border">
        <Button variant="outline" className="gap-2">
          <Save className="w-4 h-4" />
          Save as Custom Profile
        </Button>
      </div>
    </div>
  )

  const renderAdvancedTab = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium mb-4">Advanced Scan Settings</h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-4">
            <div>
              <label className="font-medium block mb-2">Resolution (DPI)</label>
              <select
                value={scanSettings.dpi}
                onChange={(e) => setScanSettings(prev => ({ ...prev, dpi: Number(e.target.value) }))}
                className="w-full px-3 py-2 bg-background border border-border rounded-md"
                title="Select Resolution (DPI)"
              >
                <option value={150}>150 DPI - Draft</option>
                <option value={200}>200 DPI - Good</option>
                <option value={300}>300 DPI - High</option>
                <option value={400}>400 DPI - OCR</option>
                <option value={600}>600 DPI - Archive</option>
                <option value={1200}>1200 DPI - Maximum</option>
              </select>
            </div>

            <div>
              <label className="font-medium block mb-2">Color Mode</label>
              <select
                value={scanSettings.colorMode}
                onChange={(e) => setScanSettings(prev => ({ ...prev, colorMode: e.target.value }))}
                className="w-full px-3 py-2 bg-background border border-border rounded-md"
                title="Select Color Mode"
              >
                <option value="Color">Color</option>
                <option value="Grayscale">Grayscale</option>
                <option value="Black & White">Black & White</option>
              </select>
            </div>

            <div>
              <label className="font-medium block mb-2">Paper Size</label>
              <select
                value={scanSettings.paperSize}
                onChange={(e) => setScanSettings(prev => ({ ...prev, paperSize: e.target.value }))}
                className="w-full px-3 py-2 bg-background border border-border rounded-md"
                title="Select Paper Size"
              >
                <option value="A4">A4</option>
                <option value="Letter">Letter</option>
                <option value="Legal">Legal</option>
                <option value="A3">A3</option>
                <option value="Custom">Custom</option>
              </select>
            </div>
          </div>

          <div className="space-y-4">
            <div>
              <label className="font-medium block mb-2">Brightness: {scanSettings.brightness}</label>
              <input
                type="range"
                min="-100"
                max="100"
                value={scanSettings.brightness}
                onChange={(e) => setScanSettings(prev => ({ ...prev, brightness: Number(e.target.value) }))}
                className="w-full"
                title="Adjust Brightness"
              />
            </div>

            <div>
              <label className="font-medium block mb-2">Contrast: {scanSettings.contrast}</label>
              <input
                type="range"
                min="-100"
                max="100"
                value={scanSettings.contrast}
                onChange={(e) => setScanSettings(prev => ({ ...prev, contrast: Number(e.target.value) }))}
                className="w-full"
                title="Adjust Contrast"
              />
            </div>

            <div>
              <label className="font-medium block mb-2">Gamma: {scanSettings.gamma.toFixed(1)}</label>
              <input
                type="range"
                min="0.1"
                max="5.0"
                step="0.1"
                value={scanSettings.gamma}
                onChange={(e) => setScanSettings(prev => ({ ...prev, gamma: Number(e.target.value) }))}
                className="w-full"
                title="Adjust Gamma"
              />
            </div>
          </div>
        </div>
      </div>

      <div className="pt-4 border-t border-border">
        <div className="flex gap-3">
          <Button onClick={handleTestScan} variant="outline" className="gap-2">
            <Eye className="w-4 h-4" />
            Test Scan
          </Button>
          <Button variant="outline" className="gap-2">
            <Save className="w-4 h-4" />
            Save as Profile
          </Button>
        </div>
      </div>
    </div>
  )

  const renderCalibrationTab = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium mb-4">Scanner Calibration</h3>
        <p className="text-muted-foreground mb-6">
          Calibrate your scanner for optimal image quality and color accuracy.
        </p>

        <div className="space-y-4">
          <div className="glass rounded-lg p-6">
            <h4 className="font-medium mb-3">Color Calibration</h4>
            <p className="text-sm text-muted-foreground mb-4">
              Scan the provided color calibration chart to ensure accurate colors.
            </p>
            <Button className="gap-2">
              <Target className="w-4 h-4" />
              Start Color Calibration
            </Button>
          </div>

          <div className="glass rounded-lg p-6">
            <h4 className="font-medium mb-3">Resolution Test</h4>
            <p className="text-sm text-muted-foreground mb-4">
              Test scanner resolution accuracy with precision targets.
            </p>
            <Button variant="outline" className="gap-2">
              <Zap className="w-4 h-4" />
              Run Resolution Test
            </Button>
          </div>

          <div className="glass rounded-lg p-6">
            <h4 className="font-medium mb-3">Clean & Maintenance</h4>
            <p className="text-sm text-muted-foreground mb-4">
              Clean scanner glass and perform maintenance tasks.
            </p>
            <Button variant="outline" className="gap-2">
              <RotateCcw className="w-4 h-4" />
              Start Maintenance
            </Button>
          </div>
        </div>
      </div>

      <div className="pt-4 border-t border-border">
        <div className="bg-muted p-4 rounded-lg">
          <h4 className="font-medium mb-2">Calibration Status</h4>
          <div className="text-sm text-muted-foreground space-y-1">
            <div>• Color calibration: Last performed 3 days ago</div>
            <div>• Resolution test: Passed (400 DPI)</div>
            <div>• Maintenance: Due in 7 days</div>
          </div>
        </div>
      </div>
    </div>
  )

  const renderTabContent = () => {
    switch (activeTab) {
      case 'device':
        return renderDeviceTab()
      case 'profiles':
        return renderProfilesTab()
      case 'advanced':
        return renderAdvancedTab()
      case 'calibration':
        return renderCalibrationTab()
      default:
        return renderDeviceTab()
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange} className="w-[95vw] max-w-5xl h-[85vh]">
      <DialogHeader>
        <DialogTitle className="flex items-center gap-2">
          <Settings className="w-5 h-5" />
          Scanner Settings
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
                  <tab.icon className="w-5 h-5" />
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
            Settings will be applied to scanner: {scanners.find(s => s.id === selectedScanner)?.name}
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button onClick={handleSaveSettings}>
              <Save className="w-4 h-4 mr-2" />
              Save Settings
            </Button>
          </div>
        </div>
      </DialogFooter>
    </Dialog>
  )
}