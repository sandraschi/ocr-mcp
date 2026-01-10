import { create } from 'zustand';
import { apiService } from '../services/api';

export interface Job {
    id: string;
    filename: string;
    status: 'pending' | 'processing' | 'completed' | 'failed';
    progress: number;
    result?: any;
    error?: string;
    createdAt: Date;
}

interface JobState {
    jobs: Job[];
    activeJobId: string | null;
    loading: boolean;
    error: string | null;

    // Actions
    addJob: (filename: string) => string; // Returns new job ID
    updateJob: (id: string, updates: Partial<Job>) => void;
    setActiveJob: (id: string | null) => void;
    removeJob: (id: string) => void;

    // Async actions
    createJob: (file: File, options?: any) => Promise<void>;
    processBatch: (files: File[]) => Promise<void>;
    pollJobStatus: (id: string) => Promise<void>;
}

export const useJobStore = create<JobState>((set, get) => ({
    jobs: [],
    activeJobId: null,
    loading: false,
    error: null,

    addJob: (filename: string) => {
        const id = Math.random().toString(36).substring(7);
        const newJob: Job = {
            id,
            filename,
            status: 'pending',
            progress: 0,
            createdAt: new Date(),
        };
        set((state) => ({ jobs: [...state.jobs, newJob] }));
        return id;
    },

    updateJob: (id, updates) => {
        set((state) => ({
            jobs: state.jobs.map((job) =>
                job.id === id ? { ...job, ...updates } : job
            ),
        }));
    },

    setActiveJob: (id) => set({ activeJobId: id }),

    removeJob: (id) => {
        set((state) => ({
            jobs: state.jobs.filter((job) => job.id !== id),
            activeJobId: state.activeJobId === id ? null : state.activeJobId,
        }));
    },

    createJob: async (file: File, options = {}) => {
        const { addJob, updateJob } = get();
        const jobId = addJob(file.name);
        set({ loading: true, error: null, activeJobId: jobId });

        try {
            updateJob(jobId, { status: 'processing', progress: 10 });

            // Call API
            // Note: apiService.processFile currently waits for the result (sync over http)
            // If we move to async jobs with getJobStatus, we would handle it differently.
            // For now, we simulate progress or just await result.

            const result = await apiService.processFile(
                file,
                options.ocrMode || 'text',
                options.backend || 'auto'
            );

            updateJob(jobId, {
                status: 'completed',
                progress: 100,
                result
            });
        } catch (error: any) {
            console.error('Job failed:', error);
            updateJob(jobId, {
                status: 'failed',
                error: error.message || 'Unknown error'
            });
            set({ error: error.message || 'Job failed' });
        } finally {
            set({ loading: false });
        }
    },

    processBatch: async (files: File[]) => {
        const { addJob, updateJob, pollJobStatus } = get();
        set({ loading: true, error: null });

        try {
            // In this implementation, we map a batch to a single job ID for status tracking
            // although each file is represented in the locally tracked jobs
            const fileIds = files.map(f => addJob(f.name));
            fileIds.forEach(id => updateJob(id, { status: 'processing' }));

            const response = await apiService.processBatch(files);

            if (response && response.job_id) {
                set({ activeJobId: response.job_id });
                // We'll need a way to link backend job_id to our local jobs if they diverge
                // For now, we'll poll the backend job
                await pollJobStatus(response.job_id);
            } else {
                fileIds.forEach(id => updateJob(id, { status: 'completed', progress: 100 }));
            }
        } catch (error: any) {
            console.error('Batch failed:', error);
            set({ error: error.message || 'Batch failed' });
        } finally {
            set({ loading: false });
        }
    },

    pollJobStatus: async (id: string) => {
        const { updateJob } = get();
        try {
            const status = await apiService.getJobStatus(id);
            // If it's a batch job, the status might apply to multiple files
            // For now, we update the active job or a matching job
            updateJob(id, {
                status: status.status as any,
                progress: status.progress,
                result: status.result,
                error: status.error
            });
        } catch (error: any) {
            console.error('Poll failed:', error);
        }
    }
}));
