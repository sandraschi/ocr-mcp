import React, { useState, useCallback } from 'react'
import { BarChart3, TrendingUp, AlertTriangle, CheckCircle, Zap, Target, Gauge } from 'lucide-react'
import { Button } from '../components/ui/Button'
import { cn } from '../lib/utils'

interface QualityMetric {
  name: string
  value: number
  maxValue: number
  status: 'excellent' | 'good' | 'fair' | 'poor'
  description: string
  icon: React.ReactNode
}

interface QualityReport {
  overall: number
  metrics: QualityMetric[]
  recommendations: string[]
  timestamp: Date
}

export function QualityPage() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [qualityReport, setQualityReport] = useState<QualityReport | null>(null)

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setSelectedFile(file)
      setQualityReport(null)
    }
  }, [])

  const handleAnalyzeQuality = useCallback(async () => {
    if (!selectedFile) return

    setIsAnalyzing(true)

    // Simulate quality analysis
    await new Promise(resolve => setTimeout(resolve, 3000))

    // Generate mock quality report
    const mockReport: QualityReport = {
      overall: 82.5,
      timestamp: new Date(),
      metrics: [
        {
          name: 'OCR Accuracy',
          value: 94.2,
          maxValue: 100,
          status: 'excellent',
          description: 'Text recognition accuracy is excellent',
          icon: <CheckCircle className="w-5 h-5" />
        },
        {
          name: 'Image Quality',
          value: 76.8,
          maxValue: 100,
          status: 'good',
          description: 'Image quality is good but could be improved',
          icon: <TrendingUp className="w-5 h-5" />
        },
        {
          name: 'Layout Preservation',
          value: 89.1,
          maxValue: 100,
          status: 'excellent',
          description: 'Document layout is well preserved',
          icon: <Target className="w-5 h-5" />
        },
        {
          name: 'Noise Level',
          value: 65.3,
          maxValue: 100,
          status: 'fair',
          description: 'Some background noise detected',
          icon: <AlertTriangle className="w-5 h-5" />
        },
        {
          name: 'Contrast Ratio',
          value: 71.9,
          maxValue: 100,
          status: 'good',
          description: 'Text contrast is adequate',
          icon: <Gauge className="w-5 h-5" />
        }
      ],
      recommendations: [
        'Consider increasing image resolution for better OCR accuracy',
        'Apply noise reduction preprocessing to improve quality score',
        'Ensure adequate lighting when scanning documents',
        'Use higher contrast settings for better text recognition'
      ]
    }

    setQualityReport(mockReport)
    setIsAnalyzing(false)
  }, [selectedFile])

  const getStatusColor = (status: QualityMetric['status']) => {
    switch (status) {
      case 'excellent':
        return 'text-green-600 bg-green-50 dark:bg-green-950'
      case 'good':
        return 'text-blue-600 bg-blue-50 dark:bg-blue-950'
      case 'fair':
        return 'text-yellow-600 bg-yellow-50 dark:bg-yellow-950'
      case 'poor':
        return 'text-red-600 bg-red-50 dark:bg-red-950'
      default:
        return 'text-gray-600 bg-gray-50 dark:bg-gray-950'
    }
  }

  const getOverallScoreColor = (score: number) => {
    if (score >= 90) return 'text-green-600'
    if (score >= 70) return 'text-blue-600'
    if (score >= 50) return 'text-yellow-600'
    return 'text-red-600'
  }

  const getOverallScoreLabel = (score: number) => {
    if (score >= 90) return 'Excellent'
    if (score >= 70) return 'Good'
    if (score >= 50) return 'Fair'
    return 'Poor'
  }

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Quality Assessment</h1>
        <p className="text-muted-foreground">
          Comprehensive document quality analysis with actionable recommendations for optimal OCR results.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* File Selection & Controls */}
        <div className="lg:col-span-1 space-y-4">
          <div className="glass rounded-lg p-4">
            <h3 className="font-medium mb-4">Quality Analysis</h3>

            <div className="space-y-4">
              <input
                type="file"
                accept=".pdf,image/*"
                onChange={handleFileSelect}
                className="hidden"
                id="quality-file-input"
              />

              <Button asChild className="w-full">
                <label htmlFor="quality-file-input" className="cursor-pointer">
                  {selectedFile ? 'Change Document' : 'Select Document'}
                </label>
              </Button>

              {selectedFile && (
                <div className="p-3 bg-muted rounded-lg">
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-8 bg-primary rounded flex items-center justify-center">
                      <span className="text-primary-foreground text-xs font-bold">
                        {selectedFile.name.split('.').pop()?.toUpperCase()}
                      </span>
                    </div>
                    <div>
                      <p className="text-sm font-medium">{selectedFile.name}</p>
                      <p className="text-xs text-muted-foreground">
                        {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                      </p>
                    </div>
                  </div>
                </div>
              )}

              <Button
                onClick={handleAnalyzeQuality}
                disabled={!selectedFile || isAnalyzing}
                className="w-full gap-2"
              >
                <BarChart3 className="w-4 h-4" />
                {isAnalyzing ? 'Analyzing...' : 'Analyze Quality'}
              </Button>
            </div>
          </div>

          {/* Analysis Progress */}
          {isAnalyzing && (
            <div className="glass rounded-lg p-4">
              <h4 className="font-medium mb-3">Analysis Progress</h4>
              <div className="space-y-2">
                <div className="w-full bg-muted rounded-full h-2">
                  <div className="bg-primary h-2 rounded-full animate-pulse w-3/4" />
                </div>
                <p className="text-sm text-muted-foreground text-center">
                  Running quality assessment...
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Quality Results */}
        <div className="lg:col-span-2">
          {qualityReport ? (
            <div className="space-y-6">
              {/* Overall Score */}
              <div className="glass rounded-lg p-6 text-center">
                <div className="mb-4">
                  <div className={cn(
                    'text-6xl font-bold mb-2',
                    getOverallScoreColor(qualityReport.overall)
                  )}>
                    {qualityReport.overall.toFixed(1)}
                  </div>
                  <div className="text-xl font-medium text-muted-foreground">
                    {getOverallScoreLabel(qualityReport.overall)} Quality
                  </div>
                </div>

                <div className="flex justify-center gap-4 text-sm text-muted-foreground">
                  <div>Analyzed: {qualityReport.timestamp.toLocaleString()}</div>
                  <div>•</div>
                  <div>5 quality metrics evaluated</div>
                </div>
              </div>

              {/* Detailed Metrics */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {qualityReport.metrics.map((metric, index) => (
                  <div key={index} className="glass rounded-lg p-4">
                    <div className="flex items-center gap-3 mb-3">
                      <div className={cn('p-2 rounded-lg', getStatusColor(metric.status))}>
                        {metric.icon}
                      </div>
                      <div>
                        <h4 className="font-medium">{metric.name}</h4>
                        <p className="text-sm text-muted-foreground">{metric.value.toFixed(1)}%</p>
                      </div>
                    </div>

                    <div className="mb-2">
                      <div className="w-full bg-muted rounded-full h-2">
                        <div
                          className="h-2 rounded-full transition-all duration-500"
                          style={{
                            width: `${(metric.value / metric.maxValue) * 100}%`,
                            backgroundColor: metric.status === 'excellent' ? '#10b981' :
                                           metric.status === 'good' ? '#3b82f6' :
                                           metric.status === 'fair' ? '#f59e0b' : '#ef4444'
                          }}
                        />
                      </div>
                    </div>

                    <p className="text-xs text-muted-foreground">{metric.description}</p>
                  </div>
                ))}
              </div>

              {/* Recommendations */}
              <div className="glass rounded-lg p-4">
                <div className="flex items-center gap-2 mb-4">
                  <Zap className="w-5 h-5 text-primary" />
                  <h3 className="font-medium">Recommendations</h3>
                </div>

                <div className="space-y-3">
                  {qualityReport.recommendations.map((recommendation, index) => (
                    <div key={index} className="flex items-start gap-3 p-3 bg-muted/50 rounded-lg">
                      <div className="w-6 h-6 bg-primary text-primary-foreground rounded-full flex items-center justify-center text-xs font-medium flex-shrink-0 mt-0.5">
                        {index + 1}
                      </div>
                      <p className="text-sm">{recommendation}</p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex gap-3">
                <Button variant="outline" className="gap-2">
                  <BarChart3 className="w-4 h-4" />
                  Export Report
                </Button>
                <Button className="gap-2">
                  <Zap className="w-4 h-4" />
                  Optimize Document
                </Button>
              </div>
            </div>
          ) : (
            <div className="glass rounded-lg p-8 text-center">
              <BarChart3 className="w-16 h-16 mx-auto mb-4 text-muted-foreground" />
              <h3 className="text-lg font-medium mb-2">Quality Assessment</h3>
              <p className="text-muted-foreground mb-4">
                Upload a document to analyze its quality for optimal OCR processing.
              </p>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                <div className="p-3 bg-muted rounded-lg">
                  <div className="font-medium text-green-600">OCR Accuracy</div>
                  <div className="text-muted-foreground">Text recognition quality</div>
                </div>
                <div className="p-3 bg-muted rounded-lg">
                  <div className="font-medium text-blue-600">Image Quality</div>
                  <div className="text-muted-foreground">Resolution and clarity</div>
                </div>
                <div className="p-3 bg-muted rounded-lg">
                  <div className="font-medium text-purple-600">Layout Preservation</div>
                  <div className="text-muted-foreground">Structure integrity</div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}