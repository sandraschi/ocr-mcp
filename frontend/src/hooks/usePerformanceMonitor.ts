import { useEffect, useRef } from 'react'

interface PerformanceMetrics {
  loadTime: number
  domContentLoaded: number
  firstPaint: number
  firstContentfulPaint: number
  largestContentfulPaint: number
  cumulativeLayoutShift: number
  firstInputDelay: number
  memoryUsage?: number
}

export function usePerformanceMonitor() {
  const metricsRef = useRef<Partial<PerformanceMetrics>>({})

  useEffect(() => {
    // Measure initial load time
    const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming
    if (navigation) {
      metricsRef.current.loadTime = navigation.loadEventEnd - navigation.fetchStart
      metricsRef.current.domContentLoaded = navigation.domContentLoadedEventEnd - navigation.fetchStart
    }

    // Monitor Core Web Vitals
    const observer = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        switch (entry.entryType) {
          case 'paint':
            if (entry.name === 'first-paint') {
              metricsRef.current.firstPaint = entry.startTime
            } else if (entry.name === 'first-contentful-paint') {
              metricsRef.current.firstContentfulPaint = entry.startTime
            }
            break

          case 'largest-contentful-paint':
            metricsRef.current.largestContentfulPaint = entry.startTime
            break

          case 'layout-shift':
            metricsRef.current.cumulativeLayoutShift =
              (metricsRef.current.cumulativeLayoutShift || 0) + (entry as any).value
            break

          case 'first-input':
            metricsRef.current.firstInputDelay = (entry as any).processingStart - entry.startTime
            break
        }
      }
    })

    try {
      observer.observe({ entryTypes: ['paint', 'largest-contentful-paint', 'layout-shift', 'first-input'] })
    } catch (e) {
      console.warn('Performance monitoring not fully supported')
    }

    // Memory monitoring (Chrome only)
    const monitorMemory = () => {
      if ('memory' in performance) {
        const memory = (performance as any).memory
        metricsRef.current.memoryUsage = memory.usedJSHeapSize / 1048576 // Convert to MB
      }
    }

    // Check memory every 30 seconds
    const memoryInterval = setInterval(monitorMemory, 30000)

    return () => {
      observer.disconnect()
      clearInterval(memoryInterval)
    }
  }, [])

  // Function to get current metrics
  const getMetrics = (): Partial<PerformanceMetrics> => {
    return { ...metricsRef.current }
  }

  // Function to report metrics (could send to analytics service)
  const reportMetrics = () => {
    const metrics = getMetrics()
    console.log('Performance Metrics:', metrics)

    // In production, send to analytics/monitoring service
    // analytics.track('performance_metrics', metrics)

    return metrics
  }

  return { getMetrics, reportMetrics }
}