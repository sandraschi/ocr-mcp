import React, { useState, useCallback } from 'react'
import { Sliders, Sun, Contrast, Image as ImageIcon, Zap, RotateCcw, Save } from 'lucide-react'
import { Button } from '../components/ui/Button'
import { cn } from '../lib/utils'

interface Filter {
    id: string
    name: string
    icon: React.ReactNode
    min: number
    max: number
    default: number
}

const FILTERS: Filter[] = [
    { id: 'brightness', name: 'Brightness', icon: <Sun className="w-4 h-4" />, min: 0, max: 200, default: 100 },
    { id: 'contrast', name: 'Contrast', icon: <Contrast className="w-4 h-4" />, min: 0, max: 200, default: 100 },
    { id: 'sharpness', name: 'Sharpness', icon: <Zap className="w-4 h-4" />, min: 0, max: 200, default: 100 },
]

export function PreprocessingPage() {
    const [selectedImage, setSelectedImage] = useState<File | null>(null)
    const [previewUrl, setPreviewUrl] = useState<string | null>(null)
    const [filterValues, setFilterValues] = useState<Record<string, number>>(
        FILTERS.reduce((acc, f) => ({ ...acc, [f.id]: f.default }), {})
    )

    const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0]
        if (file) {
            setSelectedImage(file)
            setPreviewUrl(URL.createObjectURL(file))
        }
    }, [])

    const handleFilterChange = (id: string, value: number) => {
        setFilterValues(prev => ({ ...prev, [id]: value }))
    }

    const handleReset = () => {
        setFilterValues(FILTERS.reduce((acc, f) => ({ ...acc, [f.id]: f.default }), {}))
    }

    const getPreviewStyle = () => {
        const { brightness, contrast, sharpness } = filterValues
        return {
            filter: `brightness(${brightness}%) contrast(${contrast}%) saturate(${sharpness}%)`,
        }
    }

    return (
        <div className="p-6 max-w-6xl mx-auto">
            <div className="mb-8">
                <h1 className="text-3xl font-bold mb-2">Image Preprocessing</h1>
                <p className="text-muted-foreground">
                    Enhance document quality before OCR extraction with professional image filters and adjustments.
                </p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Controls */}
                <div className="lg:col-span-1 space-y-6">
                    <div className="glass rounded-xl p-6 space-y-6">
                        <div className="space-y-4">
                            <h3 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">Document Source</h3>
                            <input
                                type="file"
                                accept="image/*"
                                onChange={handleFileSelect}
                                className="hidden"
                                id="preprocess-file-input"
                            />
                            <Button asChild className="w-full">
                                <label htmlFor="preprocess-file-input" className="cursor-pointer">
                                    <ImageIcon className="w-4 h-4 mr-2" />
                                    {selectedImage ? 'Change Image' : 'Select Image'}
                                </label>
                            </Button>
                        </div>

                        {selectedImage && (
                            <>
                                <div className="space-y-6">
                                    <h3 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">Adjustments</h3>
                                    {FILTERS.map((filter) => (
                                        <div key={filter.id} className="space-y-2">
                                            <div className="flex items-center justify-between">
                                                <label className="text-sm font-medium flex items-center gap-2">
                                                    {filter.icon}
                                                    {filter.name}
                                                </label>
                                                <span className="text-xs font-mono text-muted-foreground">
                                                    {filterValues[filter.id]}%
                                                </span>
                                            </div>
                                            <input
                                                type="range"
                                                min={filter.min}
                                                max={filter.max}
                                                value={filterValues[filter.id]}
                                                onChange={(e) => handleFilterChange(filter.id, parseInt(e.target.value))}
                                                className="w-full h-1.5 bg-muted rounded-lg appearance-none cursor-pointer accent-primary"
                                            />
                                        </div>
                                    ))}
                                </div>

                                <div className="pt-4 flex gap-3">
                                    <Button variant="outline" className="flex-1 gap-2" onClick={handleReset}>
                                        <RotateCcw className="w-4 h-4" />
                                        Reset
                                    </Button>
                                    <Button className="flex-1 gap-2">
                                        <Save className="w-4 h-4" />
                                        Apply
                                    </Button>
                                </div>
                            </>
                        )}
                    </div>
                </div>

                {/* Preview Area */}
                <div className="lg:col-span-2">
                    <div className="glass rounded-xl overflow-hidden flex flex-col min-h-[500px]">
                        <div className="bg-muted/50 p-4 border-b border-border flex items-center justify-between">
                            <h3 className="text-sm font-medium">Image Preview</h3>
                            {selectedImage && (
                                <div className="text-xs text-muted-foreground">
                                    {selectedImage.name}
                                </div>
                            )}
                        </div>

                        <div className="flex-1 flex items-center justify-center p-8 bg-black/5 dark:bg-white/5">
                            {previewUrl ? (
                                <div className="relative group max-w-full max-h-full shadow-2xl rounded-lg overflow-hidden transition-all duration-300">
                                    <img
                                        src={previewUrl}
                                        alt="Preprocessing Preview"
                                        className="max-w-full max-h-[600px] object-contain transition-all duration-300"
                                        style={getPreviewStyle()}
                                    />
                                </div>
                            ) : (
                                <div className="text-center">
                                    <ImageIcon className="w-16 h-16 mx-auto mb-4 text-muted-foreground opacity-20" />
                                    <p className="text-muted-foreground">No image selected for preprocessing</p>
                                </div>
                            )}
                        </div>

                        <div className="bg-muted/30 p-3 border-t border-border flex items-center justify-center gap-4 text-[10px] text-muted-foreground uppercase tracking-widest">
                            <span>Optimized Preview</span>
                            <span>•</span>
                            <span>Hardware Acceleration On</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}
