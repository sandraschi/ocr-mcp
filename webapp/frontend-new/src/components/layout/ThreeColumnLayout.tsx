import React from 'react'
import { Topbar } from './Topbar'
import { LeftSidebar } from './LeftSidebar'
import { RightSidebar } from './RightSidebar'
import { MainContent } from './MainContent'
import { useLayoutStore } from '../../stores/layoutStore'

interface ThreeColumnLayoutProps {
  children: React.ReactNode
}

export function ThreeColumnLayout({ children }: ThreeColumnLayoutProps) {
  const { leftSidebarOpen, rightSidebarOpen } = useLayoutStore()

  return (
    <div className="min-h-screen flex flex-col">
      {/* Topbar */}
      <Topbar />

      {/* Main Layout */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left Sidebar */}
        <LeftSidebar isOpen={leftSidebarOpen} />

        {/* Main Content */}
        <MainContent>
          {children}
        </MainContent>

        {/* Right Sidebar */}
        <RightSidebar isOpen={rightSidebarOpen} />
      </div>
    </div>
  )
}