import { Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter } from 'react-router-dom'
import { ThemeProvider } from '@components/providers/ThemeProvider'
import { ErrorBoundary } from '@components/providers/ErrorBoundary'
import { Toaster } from '@components/ui/Toaster'
import { UploadPage } from '@pages/UploadPage'
import { BatchPage } from '@pages/BatchPage'
import { ScannerPage } from '@pages/ScannerPage'
import { AnalysisPage } from '@pages/AnalysisPage'
import { QualityPage } from '@pages/QualityPage'
import { SettingsPage } from '@pages/SettingsPage'
import { PreprocessingPage } from '@pages/PreprocessingPage'
import { ConversionPage } from '@pages/ConversionPage'
import { usePerformanceMonitor } from '@hooks/usePerformanceMonitor'
import { Topbar } from './components/layout/Topbar'
import { LeftSidebar } from './components/layout/LeftSidebar'
import { LogModal } from './components/modals/LogModal'
import { useState } from 'react'
import { cn } from './lib/utils'
import { useLayoutStore } from './stores/layoutStore'

// Placeholder components for missing pages
const PlaceholderPage = ({ title }: { title: string }) => (
  <div className="p-6 max-w-4xl mx-auto">
    <div className="mb-8">
      <h1 className="text-3xl font-bold mb-2">{title}</h1>
      <p className="text-muted-foreground">This feature is coming soon!</p>
    </div>
    <div className="glass rounded-lg p-8 text-center">
      <div className="w-16 h-16 mx-auto mb-4 bg-primary/10 rounded-full flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin"></div>
      </div>
      <h3 className="text-lg font-medium mb-2">Under Development</h3>
      <p className="text-muted-foreground">This page is currently being built. Check back soon!</p>
    </div>
  </div>
)

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      gcTime: 1000 * 60 * 10, // 10 minutes
    },
  },
})

function App() {
  const { leftSidebarOpen } = useLayoutStore()
  const [isLogModalOpen, setIsLogModalOpen] = useState(false)

  // Monitor performance in production
  usePerformanceMonitor()

  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <ThemeProvider>
            <div className="min-h-screen bg-background text-foreground">
              <Topbar />

              <div className="flex pt-14 h-screen overflow-hidden">
                <LeftSidebar
                  isOpen={leftSidebarOpen}
                  onOpenLogs={() => setIsLogModalOpen(true)}
                />

                <main className={cn(
                  "flex-1 overflow-auto transition-all duration-300 bg-background/30 p-6 h-[calc(100vh-3.5rem)]",
                  leftSidebarOpen ? "ml-64" : "ml-0"
                )}>
                  <Routes>
                    <Route path="/" element={<Navigate to="/upload" replace />} />
                    <Route path="/upload" element={<UploadPage />} />
                    <Route path="/batch" element={<BatchPage />} />
                    <Route path="/scanner" element={<ScannerPage />} />
                    <Route path="/preprocessing" element={<PreprocessingPage />} />
                    <Route path="/analysis" element={<AnalysisPage />} />
                    <Route path="/quality" element={<QualityPage />} />
                    <Route path="/pipelines" element={<PlaceholderPage title="Custom Pipelines" />} />
                    <Route path="/optimization" element={<PlaceholderPage title="Auto-Optimization" />} />
                    <Route path="/conversion" element={<ConversionPage />} />
                    <Route path="/export" element={<PlaceholderPage title="Export & Download" />} />
                    <Route path="/settings" element={<SettingsPage />} />
                    <Route path="*" element={<Navigate to="/upload" replace />} />
                  </Routes>
                </main>
              </div>

              <LogModal
                open={isLogModalOpen}
                onOpenChange={setIsLogModalOpen}
              />
            </div>
            <Toaster />
          </ThemeProvider>
        </BrowserRouter>
      </QueryClientProvider>
    </ErrorBoundary>
  )
}

export default App