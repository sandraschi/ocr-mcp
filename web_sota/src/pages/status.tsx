import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { AlertCircle, RefreshCw, Activity, Terminal } from "lucide-react";

export function Status() {
    const [jobId, setJobId] = useState("");
    const [jobData, setJobData] = useState<any>(null);
    const [loading, setLoading] = useState(false);

    const checkStatus = async () => {
        if (!jobId) return;
        setLoading(true);
        try {
            const res = await fetch(`/api/job/${jobId}`);
            if (res.ok) {
                const data = await res.json();
                setJobData(data);
            } else {
                setJobData({ error: "Job trace not found. Either it expired, or the ID is invalid." });
            }
        } catch (err: unknown) {
            setJobData({ error: err instanceof Error ? err.message : "Network error" });
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="space-y-6">
            <h1 className="text-3xl font-bold tracking-tight text-slate-100">Job Status & Monitor</h1>

            <Card className="bg-slate-900/50 border-slate-800 backdrop-blur-xl">
                <CardHeader>
                    <CardTitle className="text-slate-100 flex items-center gap-2">
                        <Activity className="w-5 h-5 text-emerald-400" /> Trace Job Queue
                    </CardTitle>
                    <CardDescription className="text-slate-400">Enter a Job ID to track asynchronous OCR, export, or optimization tasks.</CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                    <div className="flex gap-4">
                        <input
                            type="text"
                            placeholder="e.g. job_1234abcd5678"
                            className="flex-1 rounded-md border-0 py-2 px-3 bg-slate-950 text-slate-100 ring-1 ring-inset ring-slate-800 focus:ring-2 focus:ring-blue-600 sm:text-sm sm:leading-6"
                            value={jobId}
                            onChange={(e) => setJobId(e.target.value)}
                        />
                        <Button onClick={checkStatus} disabled={loading || !jobId} className="bg-slate-800 hover:bg-slate-700 text-white">
                            {loading ? <RefreshCw className="w-4 h-4 mr-2 animate-spin" /> : <Terminal className="w-4 h-4 mr-2" />}
                            Check
                        </Button>
                    </div>

                    {jobData && (
                        <div className="p-4 rounded-md bg-slate-950 border border-slate-800 font-mono text-xs overflow-auto">
                            {jobData.error ? (
                                <div className="text-red-400 flex items-center gap-2">
                                    <AlertCircle className="w-4 h-4" /> {jobData.error}
                                </div>
                            ) : (
                                <pre className="text-slate-300">
                                    {JSON.stringify(jobData, null, 2)}
                                </pre>
                            )}
                        </div>
                    )}
                </CardContent>
            </Card>
        </div>
    );
}
