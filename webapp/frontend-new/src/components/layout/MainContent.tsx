import React from 'react'

interface MainContentProps {
  children: React.ReactNode
}

export function MainContent({ children }: MainContentProps) {
  return (
    <main className="flex-1 bg-background transition-all duration-300 ease-out">
      <div className="h-full overflow-auto">
        {children}
      </div>
    </main>
  )
}