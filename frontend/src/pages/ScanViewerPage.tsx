import { useState, useCallback } from 'react'
import { useScannerStore } from '../stores/scannerStore'
import { ScanViewer } from '../components/ui/ScanViewer'
import { apiService } from '../services/api'
import { Button } from '../components/ui/Button'
import { Printer, FileText, AlertCircle } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

export function ScanViewerPage() {
  const { scanResult, scanning } = useScannerStore()
  const navigate = useNavigate()
  const [selection, setSelection] = useState<any>(null)
  const handleSetSelection = useCallback((sel: any) => setSelection(sel), []);
  const [isProcessingSelection, setIsProcessingSelection] = useState(false)
  const [ocrResult, setOcrResult] = useState<string | null>(null)

  const imageUrl = scanResult?.success 
    ? `${apiService.getApiBaseUrl()}${scanResult.image_path}`
    : null

  const handleSelectionProcess = async () => {
    if (!selection || !scanResult) return
    
    setIsProcessingSelection(true)
    try {
      const formData = new FormData()
      formData.append('image_path', scanResult.image_path)
      formData.append('x', selection.x.toString())
      formData.append('y', selection.y.toString())
      formData.append('width', selection.width.toString())
      formData.append('height', selection.height.toString())
      formData.append('backend', 'auto')
      
      const result = await apiService.ocrSelection(formData)
      if (result && result.text) {
        setOcrResult(result.text)
      } else {
        setOcrResult("No text found in selection.")
      }
    } catch (error) {
      console.error('OCR Selection failed:', error)
      setOcrResult("Error processing OCR selection.")
    } finally {
      setIsProcessingSelection(false)
    }
  }

  if (scanning) {
    return (
      <div className="flex flex-col items-center justify-center h-full">
        <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin mb-4"></div>
        <p className="text-lg font-medium">Scanning in progress...</p>
      </div>
    )
  }

  if (!imageUrl) {
    return (
      <div className="flex flex-col items-center justify-center h-full max-w-md mx-auto text-center p-6">
        <div className="w-20 h-20 bg-muted rounded-full flex items-center justify-center mb-6">
          <Printer className="w-10 h-10 text-muted-foreground" />
        </div>
        <h2 className="text-2xl font-bold mb-2">No Active Scan</h2>
        <p className="text-muted-foreground mb-8">
          You haven't scanned any documents in this session yet. 
          Head over to the Scanner Control to start a new scan.
        </p>
        <Button onClick={() => navigate('/scanner')} size="lg" className="w-full">
          Go to Scanner Control
        </Button>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold mb-1">Scan Viewer</h1>
          <p className="text-muted-foreground">Review your latest scan and perform OCR on specific areas.</p>
        </div>
        
        <div className="flex items-center gap-2">
          {selection && (
            <Button 
                onClick={handleSelectionProcess}
                disabled={isProcessingSelection}
                className="gap-2 bg-blue-600 hover:bg-blue-700 text-white"
            >
                <FileText className="w-4 h-4" />
                {isProcessingSelection ? 'Processing...' : 'OCR Selection'}
            </Button>
          )}
          <Button variant="outline" onClick={() => navigate('/scanner')}>
            New Scan
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-4 gap-6 flex-1 min-h-0">
        <div className="xl:col-span-3 glass rounded-lg overflow-hidden border flex flex-col h-full min-h-[600px]">
          <ScanViewer 
            imageUrl={imageUrl} 
            onSelectionChange={handleSetSelection}
            isProcessing={isProcessingSelection}
          />
        </div>

        <div className="xl:col-span-1 flex flex-col gap-6 h-full overflow-auto">
          <div className="glass rounded-lg p-4 border bg-background/50">
            <h3 className="font-semibold mb-3 flex items-center gap-2">
              <FileText className="w-4 h-4 text-primary" />
              OCR Results
            </h3>
            
            <div className="bg-muted/50 rounded p-3 min-h-[150px] text-sm font-mono whitespace-pre-wrap border italic">
              {ocrResult || (selection ? "Click 'OCR Selection' to extract text..." : "Select an area on the image to perform OCR.")}
            </div>
            
            {ocrResult && (
              <Button 
                variant="outline" 
                size="sm" 
                className="w-full mt-3"
                onClick={() => {
                  navigator.clipboard.writeText(ocrResult);
                  // toast?
                }}
              >
                Copy to Clipboard
              </Button>
            )}
          </div>

          <div className="glass rounded-lg p-4 border bg-background/50">
            <h3 className="font-semibold mb-3 flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-primary" />
              Document Info
            </h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">File:</span>
                <span className="font-medium truncate ml-2" title={scanResult?.image_info?.filename}>
                  {scanResult?.image_info?.filename}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Resolution:</span>
                <span className="font-medium">{scanResult?.settings?.dpi} DPI</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Size:</span>
                <span className="font-medium">{scanResult?.image_info?.width} x {scanResult?.image_info?.height}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Mode:</span>
                <span className="font-medium uppercase">{scanResult?.settings?.color_mode}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
