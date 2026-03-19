import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Minus, Plus, Maximize, MousePointer } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface ScanViewerProps {
  imageUrl: string;
  onSelectionChange?: (box: { x: number; y: number; width: number; height: number; imgWidth: number; imgHeight: number } | null) => void;
  isProcessing?: boolean;
}

export function ScanViewer({ imageUrl, onSelectionChange, isProcessing }: ScanViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const imageRef = useRef<HTMLImageElement>(null);

  const [scale, setScale] = useState(1);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });

  // Selection state
  const [isSelecting, setIsSelecting] = useState(false);
  const [selectionMode, setSelectionMode] = useState(false);
  const [selectionStart, setSelectionStart] = useState({ x: 0, y: 0 });
  const [selectionEnd, setSelectionEnd] = useState({ x: 0, y: 0 });
  const [hasSelection, setHasSelection] = useState(false);

  const handleFit = useCallback(() => {
    if (containerRef.current && imageRef.current) {
        const container = containerRef.current.getBoundingClientRect();
        const img = new Image();
        img.src = imageUrl;
        img.onload = () => {
            const hRatio = container.width / img.width;
            const vRatio = container.height / img.height;
            // Use 0.95 to leave a small margin
            const newScale = Math.min(hRatio, vRatio) * 0.95;
            setScale(newScale || 1);
            setPosition({ x: 0, y: 0 });
        }
    } else {
        setScale(1);
        setPosition({ x: 0, y: 0 });
    }
  }, [imageUrl]);

  // Reset state when image changes
  useEffect(() => {
    handleFit();
    setHasSelection(false);
    // Only notify parent of null selection if the image actually changed
    // We don't include onSelectionChange in dependencies to avoid loops with unstable callbacks
  }, [imageUrl, handleFit]);

  const handleZoom = (delta: number) => {
    setScale((prevScale) => {
      return Math.max(0.1, Math.min(prevScale + delta, 5));
    });
  };

  const handleWheel = (e: React.WheelEvent) => {
    if (e.ctrlKey || e.metaKey) {
      e.preventDefault();
      handleZoom(-e.deltaY * 0.005);
    } else {
        // Pan if no modifier key
        setPosition(prev => ({
            x: prev.x - e.deltaX,
            y: prev.y - e.deltaY
        }));
    }
  };

  const clearSelection = () => {
      setHasSelection(false);
      if (onSelectionChange) onSelectionChange(null);
  };

  const getEventCoordinates = (e: React.MouseEvent | React.TouchEvent | MouseEvent | TouchEvent, element: HTMLElement) => {
    let clientX, clientY;
    if ('touches' in e) {
      clientX = e.touches[0].clientX;
      clientY = e.touches[0].clientY;
    } else {
      clientX = (e as React.MouseEvent | MouseEvent).clientX;
      clientY = (e as React.MouseEvent | MouseEvent).clientY;
    }

    const rect = element.getBoundingClientRect();
    const x = (clientX - rect.left) / scale;
    const y = (clientY - rect.top) / scale;
    return { x, y };
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    // Middle click (button 1) pans regardless of mode
    // Left click (button 0) pans if selection mode is off
    if (e.button === 1 || (!selectionMode && e.button === 0)) {
        setIsDragging(true);
        setDragStart({ x: e.clientX - position.x, y: e.clientY - position.y });
        e.preventDefault();
    } 
    // Left click in selection mode
    else if (selectionMode && e.button === 0 && imageRef.current) {
        e.preventDefault();
        e.stopPropagation(); // Stop pan
        const coords = getEventCoordinates(e, imageRef.current);
        setIsSelecting(true);
        setSelectionStart(coords);
        setSelectionEnd(coords);
        setHasSelection(true);
    }
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (isDragging) {
      setPosition({
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y,
      });
    } else if (isSelecting && imageRef.current) {
        setSelectionEnd(getEventCoordinates(e, imageRef.current));
    }
  };

  const handleMouseUp = () => {
    setIsDragging(false);
    
    if (isSelecting && imageRef.current) {
        setIsSelecting(false);
        // Calculate and report selection
        if (onSelectionChange && imageRef.current.naturalWidth) {
            const naturalW = imageRef.current.naturalWidth;
            const naturalH = imageRef.current.naturalHeight;
            const renderedW = imageRef.current.width;
            const renderedH = imageRef.current.height;

            const scaleX = naturalW / renderedW;
            const scaleY = naturalH / renderedH;

            const x0 = Math.min(selectionStart.x, selectionEnd.x);
            const y0 = Math.min(selectionStart.y, selectionEnd.y);
            const w = Math.abs(selectionStart.x - selectionEnd.x);
            const h = Math.abs(selectionStart.y - selectionEnd.y);

            // Ignore tiny selections (accidental clicks)
            if (w > 10 && h > 10) {
                 onSelectionChange({
                    x: Math.round(x0 * scaleX),
                    y: Math.round(y0 * scaleY),
                    width: Math.round(w * scaleX),
                    height: Math.round(h * scaleY),
                    imgWidth: naturalW,
                    imgHeight: naturalH
                });
            } else {
                setHasSelection(false);
                onSelectionChange(null);
            }
        }
    }
  };

  useEffect(() => {
    const handleMouseUpGlobal = () => {
      setIsDragging(false);
      setIsSelecting(false);
    };

    window.addEventListener('mouseup', handleMouseUpGlobal);
    return () => window.removeEventListener('mouseup', handleMouseUpGlobal);
  }, []);

  // Calculate selection box style
  const selectionStyle = hasSelection ? {
    left: `${Math.min(selectionStart.x, selectionEnd.x)}px`,
    top: `${Math.min(selectionStart.y, selectionEnd.y)}px`,
    width: `${Math.abs(selectionStart.x - selectionEnd.x)}px`,
    height: `${Math.abs(selectionStart.y - selectionEnd.y)}px`,
  } : {};

  return (
    <div className="flex flex-col h-full bg-background/50 rounded-lg border overflow-hidden">
      <div className="flex items-center justify-between p-2 border-b bg-muted/30">
        <div className="flex items-center gap-1">
          <Button 
            variant={selectionMode ? "default" : "outline"} 
            size="sm" 
            onClick={() => {
                setSelectionMode(!selectionMode);
                if (selectionMode) {
                    clearSelection();
                }
            }}
            className="gap-2"
            title="Drag to select an area for OCR"
          >
            <MousePointer className="w-4 h-4" />
            <span className="hidden sm:inline">{selectionMode ? 'Stop Selecting' : 'Select Area'}</span>
          </Button>

          {hasSelection && (
             <Button variant="ghost" size="sm" onClick={clearSelection}>
                 Clear
             </Button>
          )}
        </div>
        <div className="flex items-center gap-1">
          <Button variant="ghost" size="icon" onClick={() => handleZoom(-0.2)} title="Zoom Out (Ctrl+Wheel Down)">
            <Minus className="w-4 h-4" />
          </Button>
          <span className="text-xs font-mono w-12 text-center">{Math.round(scale * 100)}%</span>
          <Button variant="ghost" size="icon" onClick={() => handleZoom(0.2)} title="Zoom In (Ctrl+Wheel Up)">
            <Plus className="w-4 h-4" />
          </Button>
          <Button variant="ghost" size="icon" onClick={handleFit} title="Fit to screen">
            <Maximize className="w-4 h-4" />
          </Button>
        </div>
      </div>

      <div
        ref={containerRef}
        className={`flex-1 overflow-hidden relative ${selectionMode && !isDragging ? 'cursor-crosshair' : (isDragging ? 'cursor-grabbing' : 'cursor-grab')}`}
        onWheel={handleWheel}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
      >
        <div
          style={{
            transform: `translate(${position.x}px, ${position.y}px) scale(${scale})`,
            transformOrigin: '50% 50%', // Zoom from center of applied translation
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            minHeight: '100%',
            transition: isDragging || isSelecting ? 'none' : 'transform 0.1s ease-out',
          }}
        >
          <div className="relative inline-block" style={{ position: 'relative' }}>
             <img
                ref={imageRef}
                src={imageUrl}
                alt="Scan preview"
                className="max-w-none shadow-xl border bg-white"
                style={{ display: 'block' }}
                draggable={false}
              />
              
              {/* Selection overlay box */}
              {hasSelection && (
                <div 
                    className="absolute border-2 border-primary bg-primary/20 pointer-events-none"
                    style={{
                        ...selectionStyle,
                        boxShadow: '0 0 0 9999px rgba(0, 0, 0, 0.4)'
                    }}
                />
              )}
          </div>
        </div>

        {isProcessing && (
           <div className="absolute inset-0 bg-background/50 backdrop-blur-sm flex items-center justify-center">
              <div className="glass rounded-lg p-4 flex items-center gap-3 shadow-lg">
                <div className="w-5 h-5 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                <span className="font-medium">Processing Selection...</span>
              </div>
           </div>
        )}
      </div>
    </div>
  );
}
