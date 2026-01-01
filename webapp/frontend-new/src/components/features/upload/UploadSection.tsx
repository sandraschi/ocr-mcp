import React, { useCallback } from 'react'
import { Upload, FileText, X, Loader2, CheckCircle } from 'lucide-react'
import { Button } from '../../ui/Button'
import { cn } from '../../../lib/utils'
import { apiService, OCRResult } from '../../../services/api'
import { OCRResultViewer } from '../results/OCRResultViewer'

export function UploadSection() {
  const [files, setFiles] = React.useState<File[]>([])
  const [isDragOver, setIsDragOver] = React.useState(false)
  const [isProcessing, setIsProcessing] = React.useState(false)
  const [results, setResults] = React.useState<OCRResult[]>([])
  const [currentProgress, setCurrentProgress] = React.useState(0)

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)

    const droppedFiles = Array.from(e.dataTransfer.files)
    setFiles(prev => [...prev, ...droppedFiles])
  }, [])

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = Array.from(e.target.files || [])
    setFiles(prev => [...prev, ...selectedFiles])
  }, [])

  const removeFile = useCallback((index: number) => {
    setFiles(prev => prev.filter((_, i) => i !== index))
  }, [])

  const processFiles = useCallback(async () => {
    if (files.length === 0) return

    setIsProcessing(true)
    setResults([])
    setCurrentProgress(0)

    try {
      const newResults = []
      for (let i = 0; i < files.length; i++) {
        const file = files[i]
        // In a real app, we might want to run these in parallel or show individual progress
        const result = await apiService.processFile(file)
        newResults.push(result)
        setCurrentProgress(Math.round(((i + 1) / files.length) * 100))
      }
      setResults(newResults)
      // Clear files after successful upload if desired, or keep them to show status
      // setFiles([])
    } catch (error) {
      console.error('Processing failed:', error)
      // Error handling UI should be added
    } finally {
      setIsProcessing(false)
    }
  }, [files])

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Single Document Processing</h1>
        <p className="text-muted-foreground">
          Upload a document for OCR processing with advanced text extraction and analysis.
        </p>
      </div>

      {/* Upload Area */}
      <div
        className={cn(
          'border-2 border-dashed rounded-lg p-8 text-center transition-colors',
          isDragOver
            ? 'border-primary bg-primary/5'
            : 'border-border hover:border-primary/50'
        )}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <Upload className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
        <h3 className="text-lg font-medium mb-2">Drop your document here</h3>
        <p className="text-muted-foreground mb-4">
          or click to browse files (PDF, images up to 50MB)
        </p>
        <input
          type="file"
          multiple
          accept=".pdf,image/*"
          onChange={handleFileSelect}
          className="hidden"
          id="file-input"
        />
        <Button asChild>
          <label htmlFor="file-input" className="cursor-pointer">
            Choose Files
          </label>
        </Button>
      </div>

      {/* File List */}
      {files.length > 0 && (
        <div className="mt-6">
          <h3 className="text-lg font-medium mb-4">Selected Files</h3>
          <div className="space-y-2">
            {files.map((file, index) => (
              <div
                key={index}
                className="flex items-center gap-3 p-3 bg-card rounded-lg border"
              >
                <FileText className="w-5 h-5 text-muted-foreground" />
                <div className="flex-1">
                  <p className="font-medium">{file.name}</p>
                  <p className="text-sm text-muted-foreground">
                    {(file.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => removeFile(index)}
                  className="w-8 h-8 p-0"
                >
                  <X className="w-4 h-4" />
                </Button>
              </div>
            ))}
          </div>

          <div className="mt-6 flex flex-col gap-4">
            {isProcessing && (
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="flex items-center gap-2">
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Processing documents...
                  </span>
                  <span>{currentProgress}%</span>
                </div>
                <div className="w-full bg-muted rounded-full h-2 overflow-hidden">
                  <div
                    className="bg-primary h-full transition-all duration-300"
                    style={{ width: `${currentProgress}%` }}
                  />
                </div>
              </div>
            )}

            <div className="flex gap-3">
              <Button
                onClick={processFiles}
                disabled={files.length === 0 || isProcessing}
                className="flex-1"
              >
                {isProcessing ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Processing...
                  </>
                ) : (
                  'Process Documents'
                )}
              </Button>
              <Button
                variant="outline"
                onClick={() => {
                  setFiles([])
                  setResults([])
                  setCurrentProgress(0)
                }}
                disabled={isProcessing}
              >
                Clear All
              </Button>
            </div>

            {results.length > 0 && !isProcessing && (
              <div className="mt-8 space-y-6 animate-in fade-in slide-in-from-top-4 duration-500">
                <div className="p-4 bg-green-50 dark:bg-green-950/20 border border-green-200 dark:border-green-900 rounded-lg">
                  <h4 className="font-semibold text-green-800 dark:text-green-300 flex items-center gap-2 mb-2">
                    <CheckCircle className="w-5 h-5" />
                    Successfully Processed {results.length} Document(s)
                  </h4>
                  <p className="text-sm text-green-700 dark:text-green-400">
                    Results are ready. You can review the extraction details below or go to the Analysis page for more tools.
                  </p>
                </div>

                <div className="space-y-4">
                  <h3 className="text-lg font-semibold px-1">Processing Results</h3>
                  {results.map((result, idx) => (
                    <OCRResultViewer key={idx} result={result} />
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}