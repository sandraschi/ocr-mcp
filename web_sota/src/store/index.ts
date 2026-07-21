import { create } from "zustand";
import { persist } from "zustand/middleware";

interface ScanResult {
  imageUrl: string | null;
  filename: string | null;
  selection: {
    x: number;
    y: number;
    width: number;
    height: number;
    imgWidth: number;
    imgHeight: number;
  } | null;
}

interface OCRTextState {
  ocrText: string;
  ocrJobId: string | null;
  ocrStatus: "idle" | "processing" | "completed" | "failed";
  setOcrText: (text: string) => void;
  setOcrJobId: (id: string | null) => void;
  setOcrStatus: (status: "idle" | "processing" | "completed" | "failed") => void;
  clearOcr: () => void;
}

interface ScanStore {
  lastScan: ScanResult;
  lastOcrJobId: string | null;
  setLastScan: (scan: Partial<ScanResult>) => void;
  setLastOcrJobId: (id: string | null) => void;
  clearLastScan: () => void;
}

const useOcrTextStore = create<OCRTextState>()(
  persist(
    (set) => ({
      ocrText: "",
      ocrJobId: null,
      ocrStatus: "idle",
      setOcrText: (text) => set({ ocrText: text }),
      setOcrJobId: (id) => set({ ocrJobId: id }),
      setOcrStatus: (status) => set({ ocrStatus: status }),
      clearOcr: () => set({ ocrText: "", ocrJobId: null, ocrStatus: "idle" }),
    }),
    { name: "ocr-mcp-ocr-text" },
  ),
);

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
          lastScan: { ...state.lastScan, ...scan },
        })),
      setLastOcrJobId: (id) => set({ lastOcrJobId: id }),
      clearLastScan: () =>
        set({
          lastScan: { imageUrl: null, filename: null, selection: null },
        }),
    }),
    {
      name: "ocr-mcp-scan-store",
    },
  ),
);

export { useOcrTextStore };
