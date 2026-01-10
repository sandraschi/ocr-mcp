import { useState, useCallback, useEffect } from 'react'
import { Printer, Search, Camera, Settings, Play, Square, RotateCcw, ZoomIn, ZoomOut, Maximize, AlertCircle } from 'lucide-react'
import { Button } from '../components/ui/Button'
import { ScannerSettingsModal } from '../components/modals/ScannerSettingsModal'
import { useScannerStore } from '../stores/scannerStore'
import { cn } from '../lib/utils'

export function ScannerPage() {
  const {
    scanners,
    loading: scannersLoading,
    error: scannerError,
    fetchScanners,
    scanDocument,
    selectedScannerId: activeScannerId,
    selectScanner: setActiveScanner,
    scanResult,
    resetScanResult
  } = useScannerStore()

  const [isScanning, setIsScanning] = useState(false)
  const [scanSettings, setScanSettings] = useState({
    dpi: 300,
    colorMode: 'Color',
    paperSize: 'A4',
    source: 'Flatbed',
    brightness: 0,
    contrast: 0,
  })
  const [previewImage, setPreviewImage] = useState<string | null>(null)
  const [scanProgress, setScanProgress] = useState(0)
  const [showSettings, setShowSettings] = useState(false)
  const [scanError, setScanError] = useState<string | null>(null)

  useEffect(() => {
    fetchScanners()
  }, [fetchScanners])

  const selectedScanner = scanners.find(s => s.id === activeScannerId) || null

  const handleDiscoverScanners = useCallback(async () => {
    setScanError(null)
    await fetchScanners()
  }, [fetchScanners])

  const handleSelectScanner = useCallback((scanner: any) => {
    setActiveScanner(scanner.id)
  }, [setActiveScanner])

  const handlePreviewScan = useCallback(async () => {
    if (!selectedScanner || selectedScanner.status !== 'ready') return

    setIsScanning(true)
    setScanProgress(0)
    setScanError(null)

    try {
      // For preview, we'll use a lower DPI scan
      const previewSettings = {
        ...scanSettings,
        dpi: Math.min(scanSettings.dpi, 150),
      }

      // Simulate progress for UI feel
      const progressInterval = setInterval(() => {
        setScanProgress(prev => Math.min(prev + 10, 90))
      }, 200)

      await scanDocument(previewSettings)

      clearInterval(progressInterval)
      setScanProgress(100)

      const lastResult = useScannerStore.getState().scanResult
      if (lastResult?.success) {
        setPreviewImage(lastResult.image_path)
      }
    } catch (error) {
      console.error('Preview scan failed:', error)
      setScanError('Preview scan failed. Please check your scanner and try again.')
    } finally {
      setIsScanning(false)
    }
  }, [selectedScanner, scanSettings, scanDocument])

  const handleStartScan = useCallback(async () => {
    if (!selectedScanner || selectedScanner.status !== 'ready') return

    setIsScanning(true)
    setScanProgress(0)
    setScanError(null)

    try {
      // Simulate progress
      const progressInterval = setInterval(() => {
        setScanProgress(prev => Math.min(prev + 5, 95))
      }, 500)

      await scanDocument(scanSettings)

      clearInterval(progressInterval)
      setScanProgress(100)

      const lastResult = useScannerStore.getState().scanResult
      if (lastResult?.success) {
        setPreviewImage(lastResult.image_path)
        alert(`Scan completed successfully!\n\nScanned ${lastResult.image_info?.width}x${lastResult.image_info?.height} image`)
      }
    } catch (error) {
      console.error('Scan failed:', error)
      setScanError(`Scan failed: ${error instanceof Error ? error.message : 'Unknown error'}`)
    } finally {
      setIsScanning(false)
    }
  }, [selectedScanner, scanSettings, scanDocument])

  const handleCancelScan = useCallback(() => {
    setIsScanning(false)
    setScanProgress(0)
    setPreviewImage(null)
  }, [])

  return (
    <>
      <div className="p-6 max-w-6xl mx-auto">
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold mb-2">Scanner Control</h1>
              <p className="text-muted-foreground">
                Direct control of connected scanners with advanced settings and real-time preview.
              </p>
            </div>
            <Button onClick={() => setShowSettings(true)} className="gap-2">
              <Settings className="w-4 h-4" />
              Scanner Settings
            </Button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Scanner Discovery */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-semibold">Available Scanners</h2>
              <Button
                onClick={handleDiscoverScanners}
                disabled={scannersLoading}
                className="gap-2"
              >
                <Search className="w-4 h-4" />
                {scannersLoading ? 'Discovering...' : 'Discover'}
              </Button>
            </div>

            {/* Error display */}
            {scannerError && (
              <div className="glass rounded-lg p-4 border-red-200 bg-red-50 dark:bg-red-900/20">
                <div className="flex items-center gap-2 text-red-600 dark:text-red-400">
                  <AlertCircle className="w-5 h-5" />
                  <span className="font-medium">Scanner Discovery Error</span>
                </div>
                <p className="text-sm text-red-600 dark:text-red-400 mt-1">
                  {scannerError instanceof Error ? scannerError.message : 'Failed to discover scanners'}
                </p>
              </div>
            )}

            {/* Loading state */}
            {scannersLoading && (
              <div className="glass rounded-lg p-8 text-center">
                <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
                <p className="text-muted-foreground">Discovering scanners...</p>
              </div>
            )}

            {/* Empty state */}
            {!scannersLoading && !scannerError && scanners.length === 0 && (
              <div className="glass rounded-lg p-8 text-center">
                <Printer className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
                <h3 className="text-lg font-medium mb-2">No Scanners Found</h3>
                <p className="text-muted-foreground mb-4">
                  No scanners were detected. Make sure your scanner is connected and powered on.
                </p>
                <Button onClick={handleDiscoverScanners} className="gap-2">
                  <Search className="w-4 h-4" />
                  Try Again
                </Button>
              </div>
            )}

            {/* Scanner list */}
            {!scannersLoading && scanners.length > 0 && (
              <div className="space-y-3">
                {scanners.map((scanner) => (
                  <div
                    key={scanner.id}
                    className={cn(
                      'glass rounded-lg p-4 cursor-pointer transition-all hover:scale-[1.02]',
                      selectedScanner?.id === scanner.id
                        ? 'ring-2 ring-primary'
                        : 'hover:bg-background/50'
                    )}
                    onClick={() => handleSelectScanner(scanner)}
                  >
                    <div className="flex items-center gap-3">
                      <Printer className="w-6 h-6 text-primary" />
                      <div className="flex-1">
                        <h3 className="font-medium">{scanner.name}</h3>
                        <p className="text-sm text-muted-foreground">
                          {scanner.type} • {scanner.status}
                        </p>
                      </div>
                      <div className={cn(
                        'px-2 py-1 rounded-full text-xs font-medium',
                        scanner.status === 'ready'
                          ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                          : scanner.status === 'busy'
                            ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
                            : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                      )}>
                        {scanner.status}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Scan Control Panel */}
          <div className="space-y-4">
            {/* Scan Error Display */}
            {scanError && (
              <div className="glass rounded-lg p-4 border-red-200 bg-red-50 dark:bg-red-900/20">
                <div className="flex items-center gap-2 text-red-600 dark:text-red-400">
                  <AlertCircle className="w-5 h-5" />
                  <span className="font-medium">Scan Error</span>
                </div>
                <p className="text-sm text-red-600 dark:text-red-400 mt-1">{scanError}</p>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setScanError(null)}
                  className="mt-2"
                >
                  Dismiss
                </Button>
              </div>
            )}

            {selectedScanner ? (
              <>
                <div className="glass rounded-lg p-4">
                  <h3 className="font-medium mb-4">Selected Scanner</h3>
                  <div className="flex items-center gap-3">
                    <Printer className="w-5 h-5 text-primary" />
                    <div>
                      <p className="font-medium">{selectedScanner.name}</p>
                      <p className="text-sm text-muted-foreground">{selectedScanner.type}</p>
                    </div>
                  </div>
                </div>

                {/* Scan Settings */}
                <div className="glass rounded-lg p-4">
                  <h3 className="font-medium mb-4 flex items-center gap-2">
                    <Settings className="w-5 h-5" />
                    Scan Settings
                  </h3>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium mb-2">Resolution</label>
                      <select
                        value={scanSettings.dpi}
                        onChange={(e) => setScanSettings(prev => ({ ...prev, dpi: Number(e.target.value) }))}
                        className="w-full px-3 py-2 bg-background border border-border rounded-md"
                      >
                        <option value={150}>150 DPI</option>
                        <option value={300}>300 DPI</option>
                        <option value={600}>600 DPI</option>
                        <option value={1200}>1200 DPI</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium mb-2">Color Mode</label>
                      <select
                        value={scanSettings.colorMode}
                        onChange={(e) => setScanSettings(prev => ({ ...prev, colorMode: e.target.value }))}
                        className="w-full px-3 py-2 bg-background border border-border rounded-md"
                      >
                        <option value="Color">Color</option>
                        <option value="Grayscale">Grayscale</option>
                        <option value="Black & White">Black & White</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium mb-2">Paper Size</label>
                      <select
                        value={scanSettings.paperSize}
                        onChange={(e) => setScanSettings(prev => ({ ...prev, paperSize: e.target.value }))}
                        className="w-full px-3 py-2 bg-background border border-border rounded-md"
                      >
                        <option value="A4">A4</option>
                        <option value="Letter">Letter</option>
                        <option value="Legal">Legal</option>
                        <option value="A3">A3</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium mb-2">Source</label>
                      <select
                        value={scanSettings.source}
                        onChange={(e) => setScanSettings(prev => ({ ...prev, source: e.target.value }))}
                        className="w-full px-3 py-2 bg-background border border-border rounded-md"
                      >
                        <option value="Flatbed">Flatbed</option>
                        <option value="ADF">Auto Document Feeder</option>
                      </select>
                    </div>
                  </div>
                </div>

                {/* Scan Actions */}
                <div className="flex gap-3">
                  <Button
                    onClick={handlePreviewScan}
                    disabled={isScanning || selectedScanner.status !== 'ready'}
                    variant="outline"
                    className="gap-2"
                  >
                    <Camera className="w-4 h-4" />
                    Preview
                  </Button>

                  <Button
                    onClick={handleStartScan}
                    disabled={isScanning || !previewImage || selectedScanner.status !== 'ready'}
                    className="gap-2"
                  >
                    <Play className="w-4 h-4" />
                    {isScanning ? 'Scanning...' : 'Start Scan'}
                  </Button>

                  {isScanning && (
                    <Button onClick={handleCancelScan} variant="outline" className="gap-2">
                      <Square className="w-4 h-4" />
                      Cancel
                    </Button>
                  )}
                </div>

                {/* Progress */}
                {isScanning && (
                  <div className="glass rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium">Scanning Progress</span>
                      <span className="text-sm text-muted-foreground">{scanProgress}%</span>
                    </div>
                    <div className="w-full bg-muted rounded-full h-2">
                      <div
                        className="bg-primary h-2 rounded-full transition-all duration-300"
                        style={{ width: `${scanProgress}%` }}
                      />
                    </div>
                  </div>
                )}
              </>
            ) : (
              <div className="glass rounded-lg p-8 text-center">
                <Printer className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
                <h3 className="text-lg font-medium mb-2">No Scanner Selected</h3>
                <p className="text-muted-foreground">
                  Select a scanner from the list to configure scan settings and start scanning.
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Preview Area */}
        {previewImage && (
          <div className="mt-8 glass rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium">Scan Preview</h3>
              <div className="flex gap-2">
                <Button variant="outline" size="sm" className="gap-1">
                  <ZoomIn className="w-4 h-4" />
                  Zoom In
                </Button>
                <Button variant="outline" size="sm" className="gap-1">
                  <ZoomOut className="w-4 h-4" />
                  Zoom Out
                </Button>
                <Button variant="outline" size="sm" className="gap-1">
                  <Maximize className="w-4 h-4" />
                  Fit
                </Button>
                <Button variant="outline" size="sm" className="gap-1">
                  <RotateCcw className="w-4 h-4" />
                  Rotate
                </Button>
              </div>
            </div>

            <div className="bg-muted rounded-lg p-4 flex items-center justify-center min-h-[300px]">
              <div className="text-center">
                <Camera className="w-16 h-16 mx-auto mb-4 text-muted-foreground" />
                <p className="text-muted-foreground">Preview image would be displayed here</p>
                <p className="text-sm text-muted-foreground mt-2">
                  In a real implementation, this would show the scanned image
                </p>
              </div>
            </div>
          </div>
        )}
        <ScannerSettingsModal open={showSettings} onOpenChange={setShowSettings} />
      </div>
    </>
  )
}