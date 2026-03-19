import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface ScanResult {
    imageUrl: string | null;
    filename: string | null;
    selection: { x: number; y: number; width: number; height: number; imgWidth: number; imgHeight: number } | null;
}

interface ScanStore {
    lastScan: ScanResult;
    lastOcrJobId: string | null;
    setLastScan: (scan: Partial<ScanResult>) => void;
    setLastOcrJobId: (id: string | null) => void;
    clearLastScan: () => void;
}

export const useScanStore = create<ScanStore>()(
    persist(
        (set) => ({
            lastScan: {
                imageUrl: null,
                filename: null,
                selection: null,
            },
            lastOcrJobId: null,
            setLastScan: (scan) =>
                set((state) => ({
                    lastScan: { ...state.lastScan, ...scan }
                })),
            setLastOcrJobId: (id) => set({ lastOcrJobId: id }),
            clearLastScan: () =>
                set({
                    lastScan: { imageUrl: null, filename: null, selection: null }
                }),
        }),
        {
            name: 'ocr-mcp-scan-store',
        }
    )
);
