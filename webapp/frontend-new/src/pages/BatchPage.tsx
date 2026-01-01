import React, { useCallback, useState } from 'react'
import { Upload, FileText, X, Play, Pause, CheckCircle, AlertCircle } from 'lucide-react'
import { Button } from '../components/ui/Button'
import { cn } from '../lib/utils'
import { apiService } from '../services/api'

interface BatchFile {
  id: string
  file: File
  name: string
  size: number
  status: 'queued' | 'processing' | 'completed' | 'failed'
  progress: number
  error?: string
}

export function BatchPage() {
  const [files, setFiles] = useState<BatchFile[]>([])
  const [isProcessing, setIsProcessing] = useState(false)
  const [isDragOver, setIsDragOver] = useState(false)

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
    addFilesToBatch(droppedFiles)
  }, [])

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = Array.from(e.target.files || [])
    addFilesToBatch(selectedFiles)
  }, [])

  const addFilesToBatch = (newFiles: File[]) => {
    const batchFiles: BatchFile[] = newFiles.map(file => ({
      id: Date.now() + Math.random().toString(),
      file,
      name: file.name,
      size: file.size,
      status: 'queued',
      progress: 0,
    }))

    setFiles(prev => [...prev, ...batchFiles])
  }

  const removeFile = useCallback((fileId: string) => {
    setFiles(prev => prev.filter(f => f.id !== fileId))
  }, [])

  const clearAllFiles = useCallback(() => {
    setFiles([])
  }, [])

  const pollJobStatus = async (jobId: string) => {
    const pollInterval = setInterval(async () => {
      try {
        const status = await apiService.getJobStatus(jobId)

        // Update all files in this batch with the job status
        // Note: In a real multi-job system, we'd need to map files to jobs
        setFiles(prev => prev.map(f => {
          if (f.status === 'processing') {
            return {
              ...f,
              progress: status.progress,
              status: status.status === 'completed' ? 'completed'
                : status.status === 'failed' ? 'failed'
                  : 'processing'
            }
          }
          return f
        }))

        if (status.status === 'completed' || status.status === 'failed') {
          clearInterval(pollInterval)
          setIsProcessing(false)
        }
      } catch (error) {
        console.error('Polling failed:', error)
        clearInterval(pollInterval)
        setIsProcessing(false)
        setFiles(prev => prev.map(f => f.status === 'processing' ? { ...f, status: 'failed', error: 'Status check failed' } : f))
      }
    }, 1000)
  }

  const startBatchProcessing = useCallback(async () => {
    if (files.length === 0) return

    setIsProcessing(true)

    // Mark items as processing
    setFiles(prev => prev.map(f => f.status === 'queued' ? { ...f, status: 'processing' } : f))

    try {
      const batchFiles = files.filter(f => f.status === 'queued' || f.status === 'processing').map(f => f.file)
      const response = await apiService.processBatch(batchFiles)

      if (response && response.job_id) {
        await pollJobStatus(response.job_id)
      } else {
        // Fallback or immediate completion if no job ID
        setFiles(prev => prev.map(f => f.status === 'processing' ? { ...f, status: 'completed', progress: 100 } : f))
        setIsProcessing(false)
      }
    } catch (error) {
      console.error('Batch processing failed:', error)
      setFiles(prev => prev.map(f => f.status === 'processing' ? { ...f, status: 'failed', error: 'Processing initiation failed' } : f))
      setIsProcessing(false)
    }
  }, [files])

  const getStatusIcon = (status: BatchFile['status']) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-500" />
      case 'failed':
        return <AlertCircle className="w-5 h-5 text-red-500" />
      case 'processing':
        return <div className="w-5 h-5 border-2 border-primary border-t-transparent rounded-full animate-spin" />
      default:
        return <div className="w-5 h-5 border-2 border-muted-foreground border-t-transparent rounded-full" />
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
  }

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Batch Processing</h1>
        <p className="text-muted-foreground">
          Process multiple documents simultaneously with advanced batch operations and progress tracking.
        </p>
      </div>

      {/* Upload Area */}
      <div
        className={cn(
          'border-2 border-dashed rounded-lg p-8 text-center transition-colors mb-6',
          isDragOver
            ? 'border-primary bg-primary/5'
            : 'border-border hover:border-primary/50'
        )}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <Upload className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
        <h3 className="text-lg font-medium mb-2">Drop files here for batch processing</h3>
        <p className="text-muted-foreground mb-4">
          or click to browse multiple files (PDF, images up to 50MB each)
        </p>
        <input
          type="file"
          multiple
          accept=".pdf,image/*"
          onChange={handleFileSelect}
          className="hidden"
          id="batch-file-input"
        />
        <Button asChild disabled={isProcessing}>
          <label htmlFor="batch-file-input" className="cursor-pointer">
            Choose Files
          </label>
        </Button>
      </div>

      {/* File List */}
      {files.length > 0 && (
        <div className="mb-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium">Batch Queue ({files.length} files)</h3>
            <Button variant="outline" onClick={clearAllFiles} disabled={isProcessing}>
              Clear All
            </Button>
          </div>

          <div className="space-y-3 max-h-96 overflow-y-auto">
            {files.map((file) => (
              <div
                key={file.id}
                className="flex items-center gap-4 p-4 bg-card rounded-lg border"
              >
                {getStatusIcon(file.status)}
                <div className="flex-1">
                  <div className="flex items-center gap-3">
                    <FileText className="w-5 h-5 text-muted-foreground" />
                    <div>
                      <p className="font-medium">{file.name}</p>
                      <p className="text-sm text-muted-foreground">
                        {formatFileSize(file.size)}
                        {file.error && (
                          <span className="text-red-500 ml-2">• {file.error}</span>
                        )}
                      </p>
                    </div>
                  </div>

                  {file.status === 'processing' && (
                    <div className="mt-2">
                      <div className="w-full bg-muted rounded-full h-2">
                        <div
                          className="bg-primary h-2 rounded-full transition-all duration-300"
                          style={{ width: `${file.progress}%` }}
                        />
                      </div>
                      <p className="text-xs text-muted-foreground mt-1">
                        {file.progress}% complete
                      </p>
                    </div>
                  )}
                </div>

                {!isProcessing && file.status !== 'processing' && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => removeFile(file.id)}
                    className="w-8 h-8 p-0"
                  >
                    <X className="w-4 h-4" />
                  </Button>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Controls */}
      {files.length > 0 && (
        <div className="flex gap-3">
          <Button
            onClick={startBatchProcessing}
            disabled={isProcessing || files.every(f => f.status === 'completed' || f.status === 'failed')}
            className="gap-2"
          >
            <Play className="w-4 h-4" />
            {isProcessing ? 'Processing...' : 'Start Batch Processing'}
          </Button>

          {isProcessing && (
            <Button variant="outline" disabled className="gap-2">
              <Pause className="w-4 h-4" />
              Processing...
            </Button>
          )}
        </div>
      )}

      {/* Statistics */}
      {files.length > 0 && (
        <div className="mt-8 grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="glass rounded-lg p-4 text-center">
            <div className="text-2xl font-bold">{files.length}</div>
            <div className="text-sm text-muted-foreground">Total Files</div>
          </div>
          <div className="glass rounded-lg p-4 text-center">
            <div className="text-2xl font-bold text-green-600">
              {files.filter(f => f.status === 'completed').length}
            </div>
            <div className="text-sm text-muted-foreground">Completed</div>
          </div>
          <div className="glass rounded-lg p-4 text-center">
            <div className="text-2xl font-bold text-blue-600">
              {files.filter(f => f.status === 'processing').length}
            </div>
            <div className="text-sm text-muted-foreground">Processing</div>
          </div>
          <div className="glass rounded-lg p-4 text-center">
            <div className="text-2xl font-bold text-red-600">
              {files.filter(f => f.status === 'failed').length}
            </div>
            <div className="text-sm text-muted-foreground">Failed</div>
          </div>
        </div>
      )}
    </div>
  )
}