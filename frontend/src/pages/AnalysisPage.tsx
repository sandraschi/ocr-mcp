import React, { useState, useCallback } from 'react'
import { FileText, Search, Download, Loader2, CheckCircle } from 'lucide-react'
import { Button } from '../components/ui/Button'
import { apiService, OCRResult } from '../services/api'
import { OCRResultViewer } from '../components/features/results/OCRResultViewer'


export function AnalysisPage() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [analysisProgress, setAnalysisProgress] = useState(0)
  const [ocrResult, setOcrResult] = useState<OCRResult | null>(null)

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setSelectedFile(file)
      setOcrResult(null)
    }
  }, [])

  const handleAnalyze = useCallback(async () => {
    if (!selectedFile) return

    setIsAnalyzing(true)
    setAnalysisProgress(0)
    setOcrResult(null)

    try {
      // For large files, we might want to simulate progress if backend doesn't support it
      const interval = setInterval(() => {
        setAnalysisProgress(prev => Math.min(prev + 10, 90))
      }, 500)

      const result = await apiService.processFile(selectedFile)

      clearInterval(interval)
      setAnalysisProgress(100)
      setOcrResult(result)
    } catch (error) {
      console.error('Analysis failed:', error)
      alert('Analysis failed. Please try again.')
    } finally {
      setIsAnalyzing(false)
    }
  }, [selectedFile])

  const handleExport = useCallback((format: 'json' | 'csv' | 'txt') => {
    // TODO: Implement export functionality
    console.log(`Exporting as ${format}`)
  }, [])


  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Document Analysis</h1>
        <p className="text-muted-foreground">
          Advanced document analysis with text extraction, table detection, layout analysis, and quality assessment.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* File Selection & Controls */}
        <div className="lg:col-span-1 space-y-4">
          <div className="glass rounded-lg p-4">
            <h3 className="font-medium mb-4">Document Selection</h3>

            <div className="space-y-4">
              <input
                type="file"
                accept=".pdf,image/*"
                onChange={handleFileSelect}
                className="hidden"
                id="analysis-file-input"
              />

              <Button asChild className="w-full">
                <label htmlFor="analysis-file-input" className="cursor-pointer">
                  {selectedFile ? 'Change Document' : 'Select Document'}
                </label>
              </Button>

              {selectedFile && (
                <div className="p-3 bg-muted rounded-lg">
                  <div className="flex items-center gap-2">
                    <FileText className="w-4 h-4" />
                    <span className="text-sm font-medium">{selectedFile.name}</span>
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">
                    {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                </div>
              )}

              <Button
                onClick={handleAnalyze}
                disabled={!selectedFile || isAnalyzing}
                className="w-full gap-2"
              >
                <Search className="w-4 h-4" />
                {isAnalyzing ? 'Analyzing...' : 'Analyze Document'}
              </Button>
            </div>
          </div>

          {/* Analysis Progress */}
          {isAnalyzing && (
            <div className="glass rounded-lg p-4">
              <h4 className="font-medium mb-3">Analysis Progress</h4>
              <div className="space-y-2">
                <div className="w-full bg-muted rounded-full h-2">
                  <div
                    className="bg-primary h-2 rounded-full transition-all duration-300"
                    style={{ width: `${analysisProgress}%` }}
                  />
                </div>
                <p className="text-sm text-muted-foreground text-center">
                  {analysisProgress}% complete
                </p>
              </div>
            </div>
          )}

          {/* Export Options */}
          {ocrResult && !isAnalyzing && (
            <div className="glass rounded-lg p-4">
              <h4 className="font-medium mb-3">Export Results</h4>
              <div className="space-y-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleExport('json')}
                  className="w-full justify-start gap-2"
                >
                  <Download className="w-4 h-4" />
                  Export as JSON
                </Button>
              </div>
            </div>
          )}
        </div>

        {/* Results Display */}
        <div className="lg:col-span-2">
          {!ocrResult && !isAnalyzing ? (
            <div className="glass rounded-lg p-12 text-center">
              <Search className="w-16 h-16 mx-auto mb-4 text-muted-foreground opacity-20" />
              <h3 className="text-xl font-medium mb-2">Ready for Analysis</h3>
              <p className="text-muted-foreground">
                Select a document and click "Analyze Document" to extract text, tables, and more.
              </p>
            </div>
          ) : isAnalyzing ? (
            <div className="glass rounded-lg p-12 text-center">
              <Loader2 className="w-16 h-16 mx-auto mb-4 text-primary animate-spin" />
              <h3 className="text-xl font-medium mb-2">Analyzing Document...</h3>
              <p className="text-muted-foreground">
                Our AI is currently processing your document. This may take a few seconds.
              </p>
              <div className="mt-8 max-w-xs mx-auto">
                <div className="w-full bg-muted rounded-full h-2">
                  <div
                    className="bg-primary h-2 rounded-full transition-all duration-300"
                    style={{ width: `${analysisProgress}%` }}
                  />
                </div>
              </div>
            </div>
          ) : ocrResult ? (
            <div className="space-y-6">
              <div className="flex items-center justify-between mb-2">
                <h2 className="text-xl font-bold flex items-center gap-2">
                  <CheckCircle className="w-5 h-5 text-green-500" />
                  Analysis Results
                </h2>
                <div className="text-sm font-medium px-2 py-1 bg-green-100 text-green-700 rounded-md">
                  {(ocrResult.confidence * 100).toFixed(1)}% Confidence
                </div>
              </div>

              <OCRResultViewer result={ocrResult} />
            </div>
          ) : null}
        </div>
      </div>
    </div>
  )
}