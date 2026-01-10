import { create } from 'zustand';
import { apiService, Scanner, ScanResult, ScanSettings } from '../services/api';

interface ScannerState {
    scanners: Scanner[];
    selectedScannerId: string | null;
    scanning: boolean;
    loading: boolean;
    scanResult: ScanResult | null;
    error: string | null;
    lastScanSettings: ScanSettings | null;

    fetchScanners: () => Promise<void>;
    selectScanner: (id: string) => void;
    scanDocument: (settings: ScanSettings) => Promise<void>;
    resetScanResult: () => void;
}

export const useScannerStore = create<ScannerState>((set, get) => ({
    scanners: [],
    selectedScannerId: null,
    scanning: false,
    loading: false,
    scanResult: null,
    error: null,
    lastScanSettings: null,

    fetchScanners: async () => {
        set({ loading: true, error: null });
        try {
            const response = await apiService.getScanners();
            set({ scanners: response.scanners });

            // Auto-select first scanner if none selected
            const { selectedScannerId } = get();
            if (!selectedScannerId && response.scanners.length > 0) {
                set({ selectedScannerId: response.scanners[0].id });
            }
        } catch (error: any) {
            console.error('Failed to fetch scanners:', error);
            set({ error: error.message || 'Failed to fetch scanners' });
            // Use mock data if API fails (for development/demo)
            if (import.meta.env.DEV) {
                // Mock data handled by component or service if needed, 
                // but store just records the error usually.
                // We can leave it as error state.
            }
        } finally {
            set({ loading: false });
        }
    },

    selectScanner: (id: string) => {
        set({ selectedScannerId: id });
    },

    scanDocument: async (settings: ScanSettings) => {
        const { selectedScannerId } = get();
        if (!selectedScannerId) {
            set({ error: 'No scanner selected' });
            return;
        }

        set({ scanning: true, error: null, scanResult: null, lastScanSettings: settings });
        try {
            const result = await apiService.scanDocument(selectedScannerId, settings);

            if (!result.success) {
                throw new Error(result.message || 'Scan failed');
            }

            set({ scanResult: result });
        } catch (error: any) {
            console.error('Scan failed:', error);
            set({ error: error.message || 'Scan failed' });
        } finally {
            set({ scanning: false });
        }
    },

    resetScanResult: () => {
        set({ scanResult: null, error: null });
    }
}));
