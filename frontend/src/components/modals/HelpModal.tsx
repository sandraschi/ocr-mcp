import React, { useState, useMemo } from 'react'
import { HelpCircle, Search, Book, Keyboard, Settings, Upload, Activity, ChevronRight, ExternalLink } from 'lucide-react'
import { Dialog, DialogHeader, DialogTitle, DialogClose, DialogContent } from '../ui/Dialog'
import { Button } from '../ui/Button'
import { cn } from '../../lib/utils'

interface HelpTopic {
  id: string
  title: string
  description: string
  category: string
  icon: React.ReactNode
  content: string
  keywords: string[]
}

interface HelpModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function HelpModal({ open, onOpenChange }: HelpModalProps) {
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedTopic, setSelectedTopic] = useState<HelpTopic | null>(null)
  const [activeCategory, setActiveCategory] = useState<string>('all')

  const helpTopics: HelpTopic[] = [
    {
      id: 'getting-started',
      title: 'Getting Started',
      description: 'Learn the basics of using OCR-MCP',
      category: 'basics',
      icon: <Book className="w-5 h-5" />,
      keywords: ['start', 'begin', 'tutorial', 'guide'],
      content: `
# Getting Started with OCR-MCP

Welcome to OCR-MCP! This powerful tool helps you extract text from documents using advanced OCR technology.

## Quick Start

1. **Upload a Document**: Click the upload area or drag & drop files
2. **Choose Processing Options**: Select OCR backend and language
3. **Process**: Click "Process Document" to extract text
4. **View Results**: Review extracted text and download if needed

## Supported Formats

- PDF documents
- PNG, JPG, JPEG images
- TIFF images
- CBZ/CBR comic archives

## Tips for Best Results

- Use high-resolution scans (300 DPI recommended)
- Ensure good contrast between text and background
- Straighten skewed documents before processing
- Use appropriate language settings for better accuracy
      `
    },
    {
      id: 'uploading-files',
      title: 'Uploading Files',
      description: 'How to upload and manage documents',
      category: 'upload',
      icon: <Upload className="w-5 h-5" />,
      keywords: ['upload', 'files', 'drag', 'drop', 'select'],
      content: `
# Uploading Files

OCR-MCP supports multiple ways to upload your documents for processing.

## Upload Methods

### Drag & Drop
- Drag files from your file explorer
- Drop them onto the upload area
- Multiple files supported simultaneously

### File Browser
- Click "Choose Files" button
- Select multiple files using Ctrl/Cmd + click
- Browse through your file system

### Batch Processing
- Use the Batch page for processing multiple files
- Monitor progress for each file individually
- Get summary statistics after completion

## File Requirements

- **Maximum Size**: 50MB per file
- **Supported Formats**: PDF, PNG, JPG, JPEG, TIFF, BMP, CBZ, CBR
- **Pages**: Unlimited for PDFs, single page for images

## File Validation

Files are automatically validated before processing:
- Format compatibility check
- Size limit verification
- File corruption detection
      `
    },
    {
      id: 'scanner-control',
      title: 'Scanner Control',
      description: 'Direct control of connected scanners',
      category: 'scanner',
      icon: <Settings className="w-5 h-5" />,
      keywords: ['scanner', 'hardware', 'device', 'scan'],
      content: `
# Scanner Control

Directly control connected scanning hardware for seamless document digitization.

## Scanner Discovery

1. Go to the Scanner page
2. Click "Discover Scanners"
3. Select your preferred device from the list
4. Configure scan settings

## Scan Settings

### Resolution (DPI)
- **150 DPI**: Fast scanning, basic OCR
- **300 DPI**: Standard quality, good OCR accuracy
- **600 DPI**: High quality, excellent OCR results
- **1200 DPI**: Maximum quality, slower processing

### Color Mode
- **Color**: Full color reproduction
- **Grayscale**: Black and white with shades
- **Black & White**: Pure monochrome

### Paper Size
- A4, Letter, Legal, A3
- Custom sizes available

## Preview & Scan

1. **Preview**: Check scan area and settings
2. **Adjust**: Fine-tune brightness, contrast if needed
3. **Scan**: Capture final document
4. **Process**: Send to OCR engine automatically

## Troubleshooting

**Scanner not detected?**
- Ensure scanner is powered on
- Check USB connections
- Try different USB ports
- Restart OCR-MCP application

**Poor scan quality?**
- Clean scanner glass
- Adjust brightness/contrast
- Use higher DPI settings
- Ensure proper paper alignment
      `
    },
    {
      id: 'keyboard-shortcuts',
      title: 'Keyboard Shortcuts',
      description: 'Boost productivity with keyboard shortcuts',
      category: 'productivity',
      icon: <Keyboard className="w-5 h-5" />,
      keywords: ['shortcuts', 'keyboard', 'hotkeys', 'productivity'],
      content: `
# Keyboard Shortcuts

Master these shortcuts to work faster and more efficiently.

## Global Shortcuts

| Shortcut | Action |
|----------|--------|
| \`Ctrl + O\` | Open file browser |
| \`Ctrl + B\` | Go to batch processing |
| \`Ctrl + S\` | Go to scanner page |
| \`Ctrl + L\` | Open logger |
| \`Ctrl + H\` | Open help |
| \`Ctrl + ,\` | Open settings |
| \`Escape\` | Close modals/panels |

## Navigation

| Shortcut | Action |
|----------|--------|
| \`Alt + 1\` | Go to Upload page |
| \`Alt + 2\` | Go to Batch page |
| \`Alt + 3\` | Go to Scanner page |
| \`Alt + 4\` | Go to Analysis page |
| \`Alt + 5\` | Go to Quality page |

## File Operations

| Shortcut | Action |
|----------|--------|
| \`Ctrl + Enter\` | Process current file |
| \`Ctrl + Shift + S\` | Save results |
| \`Ctrl + Shift + E\` | Export results |
| \`Delete\` | Remove selected file |

## View Controls

| Shortcut | Action |
|----------|--------|
| \`F11\` | Toggle fullscreen |
| \`Ctrl + +\` | Zoom in |
| \`Ctrl + -\` | Zoom out |
| \`Ctrl + 0\` | Reset zoom |

## Accessibility

| Shortcut | Action |
|----------|--------|
| \`Tab\` | Navigate between elements |
| \`Shift + Tab\` | Navigate backwards |
| \`Enter\` | Activate button/link |
| \`Space\` | Toggle checkbox/slider |
      `
    },
    {
      id: 'activity-logging',
      title: 'Activity Logging',
      description: 'Monitor system activity and troubleshoot issues',
      category: 'advanced',
      icon: <Activity className="w-5 h-5" />,
      keywords: ['logs', 'activity', 'monitor', 'debug', 'troubleshoot'],
      content: `
# Activity Logging

Comprehensive logging system to monitor system activity and troubleshoot issues.

## Accessing Logs

1. Click the logger icon in the topbar
2. View real-time activity feed
3. Filter by log level and search content
4. Export logs for analysis

## Log Levels

### ERROR (🔴)
Critical errors that prevent normal operation
- File processing failures
- Scanner connection issues
- System resource problems

### WARNING (🟡)
Potential issues that don't stop operation
- Quality warnings
- Performance degradation
- Configuration issues

### INFO (🔵)
Normal operation information
- File processing started/completed
- Scanner connections
- System status updates

### DEBUG (⚪)
Detailed technical information
- API calls and responses
- Memory usage statistics
- Processing performance metrics

## Filtering & Search

### Level Filtering
- Click level buttons to filter logs
- Combine multiple levels for focused views
- "All" shows everything

### Text Search
- Search within log messages
- Search source components
- Search metadata and details

### Time-based Filtering
- Filter by time ranges
- Focus on recent activity
- Export specific time periods

## Export & Analysis

### JSON Export
- Complete log data with timestamps
- Structured for analysis tools
- Includes all metadata

### Troubleshooting Tips

**High Error Count?**
- Check file formats and sizes
- Verify scanner connections
- Review system resources

**Slow Processing?**
- Monitor memory usage
- Check file sizes
- Review OCR backend performance

**Connection Issues?**
- Check network connectivity
- Verify API endpoints
- Review authentication status
      `
    }
  ]

  const categories = [
    { id: 'all', label: 'All Topics', count: helpTopics.length },
    { id: 'basics', label: 'Getting Started', count: helpTopics.filter(t => t.category === 'basics').length },
    { id: 'upload', label: 'File Upload', count: helpTopics.filter(t => t.category === 'upload').length },
    { id: 'scanner', label: 'Scanner', count: helpTopics.filter(t => t.category === 'scanner').length },
    { id: 'productivity', label: 'Productivity', count: helpTopics.filter(t => t.category === 'productivity').length },
    { id: 'advanced', label: 'Advanced', count: helpTopics.filter(t => t.category === 'advanced').length },
  ]

  const filteredTopics = useMemo(() => {
    let topics = helpTopics

    // Filter by category
    if (activeCategory !== 'all') {
      topics = topics.filter(topic => topic.category === activeCategory)
    }

    // Filter by search
    if (searchTerm) {
      const term = searchTerm.toLowerCase()
      topics = topics.filter(topic =>
        topic.title.toLowerCase().includes(term) ||
        topic.description.toLowerCase().includes(term) ||
        topic.keywords.some(keyword => keyword.toLowerCase().includes(term))
      )
    }

    return topics
  }, [activeCategory, searchTerm])

  const handleTopicSelect = (topic: HelpTopic) => {
    setSelectedTopic(topic)
  }

  const handleBackToList = () => {
    setSelectedTopic(null)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange} className="w-[95vw] max-w-6xl h-[85vh]">
      <DialogHeader>
        <DialogTitle className="flex items-center gap-2">
          <HelpCircle className="w-5 h-5" />
          Help & Documentation
        </DialogTitle>
        <DialogClose onClick={() => onOpenChange(false)} />
      </DialogHeader>

      <DialogContent className="flex h-full p-0">
        <div className="flex w-full h-full">
          {/* Sidebar */}
          <div className="w-80 border-r border-border flex flex-col">
            {/* Search */}
            <div className="p-4 border-b border-border">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <input
                  type="text"
                  placeholder="Search help topics..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-ring"
                />
              </div>
            </div>

            {/* Categories */}
            <div className="p-4 border-b border-border">
              <div className="flex gap-1 overflow-x-auto">
                {categories.map((category) => (
                  <button
                    key={category.id}
                    onClick={() => setActiveCategory(category.id)}
                    className={cn(
                      'px-3 py-1.5 rounded-md text-sm whitespace-nowrap transition-colors',
                      activeCategory === category.id
                        ? 'bg-primary text-primary-foreground'
                        : 'hover:bg-muted'
                    )}
                  >
                    {category.label} ({category.count})
                  </button>
                ))}
              </div>
            </div>

            {/* Topics List */}
            <div className="flex-1 overflow-y-auto p-4">
              <div className="space-y-2">
                {filteredTopics.map((topic) => (
                  <button
                    key={topic.id}
                    onClick={() => handleTopicSelect(topic)}
                    className={cn(
                      'w-full p-3 text-left rounded-lg transition-colors hover:bg-muted',
                      selectedTopic?.id === topic.id && 'bg-muted ring-1 ring-border'
                    )}
                  >
                    <div className="flex items-start gap-3">
                      <div className="text-primary mt-0.5">
                        {topic.icon}
                      </div>
                      <div className="flex-1">
                        <h3 className="font-medium text-sm">{topic.title}</h3>
                        <p className="text-xs text-muted-foreground mt-1">
                          {topic.description}
                        </p>
                      </div>
                      <ChevronRight className="w-4 h-4 text-muted-foreground mt-1" />
                    </div>
                  </button>
                ))}

                {filteredTopics.length === 0 && (
                  <div className="text-center py-8 text-muted-foreground">
                    <Search className="w-8 h-8 mx-auto mb-2 opacity-50" />
                    <p>No topics found</p>
                    <p className="text-sm">Try adjusting your search terms</p>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Content Area */}
          <div className="flex-1 flex flex-col">
            {selectedTopic ? (
              <>
                {/* Topic Header */}
                <div className="p-6 border-b border-border">
                  <button
                    onClick={handleBackToList}
                    className="flex items-center gap-2 text-muted-foreground hover:text-foreground mb-4"
                  >
                    <ChevronRight className="w-4 h-4 rotate-180" />
                    Back to topics
                  </button>

                  <div className="flex items-center gap-3">
                    <div className="text-primary">
                      {selectedTopic.icon}
                    </div>
                    <div>
                      <h2 className="text-xl font-semibold">{selectedTopic.title}</h2>
                      <p className="text-muted-foreground">{selectedTopic.description}</p>
                    </div>
                  </div>
                </div>

                {/* Topic Content */}
                <div className="flex-1 overflow-y-auto p-6">
                  <div className="prose prose-sm max-w-none dark:prose-invert">
                    <div
                      dangerouslySetInnerHTML={{
                        __html: selectedTopic.content
                          .split('\n')
                          .map(line => {
                            // Convert markdown-style headers
                            if (line.startsWith('# ')) {
                              return `<h1 class="text-2xl font-bold mb-4">${line.slice(2)}</h1>`
                            }
                            if (line.startsWith('## ')) {
                              return `<h2 class="text-xl font-semibold mb-3 mt-6">${line.slice(3)}</h2>`
                            }
                            if (line.startsWith('### ')) {
                              return `<h3 class="text-lg font-medium mb-2 mt-4">${line.slice(4)}</h3>`
                            }
                            // Convert markdown-style lists
                            if (line.startsWith('- ')) {
                              return `<li class="mb-1">${line.slice(2)}</li>`
                            }
                            // Convert markdown-style bold
                            if (line.includes('**')) {
                              return `<p class="mb-3">${line.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')}</p>`
                            }
                            // Convert markdown-style code
                            if (line.includes('`')) {
                              return `<p class="mb-3">${line.replace(/`(.*?)`/g, '<code class="bg-muted px-1 py-0.5 rounded text-sm">$1</code>')}</p>`
                            }
                            // Regular paragraphs
                            if (line.trim()) {
                              return `<p class="mb-3">${line}</p>`
                            }
                            return line
                          })
                          .join('')
                          .replace(/<li/g, '<ul class="list-disc list-inside mb-3"><li')
                          .replace(/<\/li>\n<li/g, '</li><li')
                          .replace(/<\/li>\n([^<])/g, '</li></ul>$1')
                      }}
                    />
                  </div>
                </div>
              </>
            ) : (
              /* Welcome Screen */
              <div className="flex-1 flex items-center justify-center p-6">
                <div className="text-center max-w-md">
                  <HelpCircle className="w-16 h-16 mx-auto mb-6 text-muted-foreground" />
                  <h2 className="text-2xl font-semibold mb-4">Welcome to Help</h2>
                  <p className="text-muted-foreground mb-6">
                    Find answers to your questions, learn new features, and get the most out of OCR-MCP.
                  </p>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div className="p-4 bg-muted rounded-lg">
                      <Book className="w-6 h-6 mx-auto mb-2 text-primary" />
                      <div className="font-medium">Documentation</div>
                      <div className="text-muted-foreground">Step-by-step guides</div>
                    </div>
                    <div className="p-4 bg-muted rounded-lg">
                      <Keyboard className="w-6 h-6 mx-auto mb-2 text-primary" />
                      <div className="font-medium">Shortcuts</div>
                      <div className="text-muted-foreground">Boost productivity</div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}