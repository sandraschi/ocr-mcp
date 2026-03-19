import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import {
    BookOpen,
    HelpCircle,
    Monitor,
    Server,
    Cpu,
    FolderOpen,
} from "lucide-react";

export function Help() {
    return (
        <div className="space-y-6 max-w-4xl mx-auto pb-12">
            <h1 className="text-3xl font-bold tracking-tight text-slate-100 flex items-center gap-3">
                <HelpCircle className="w-8 h-8 text-blue-500" />
                Help & Documentation
            </h1>

            <p className="text-slate-400 text-sm -mt-2">
                OCR-MCP ships as one repo with <strong className="text-slate-300">three</strong> things to know: the{' '}
                <strong className="text-slate-300">web app</strong> (this UI), the{' '}
                <strong className="text-slate-300">MCP server</strong> (for Cursor, Claude, etc.), and the{' '}
                <strong className="text-slate-300">OCR backends</strong> (engines both surfaces use).
            </p>

            {/* —— Web application —— */}
            <Card className="bg-slate-900/50 border-slate-800 backdrop-blur-xl">
                <CardHeader>
                    <CardTitle className="text-slate-100 flex items-center gap-2">
                        <Monitor className="w-5 h-5 text-sky-400" />
                        Web application
                    </CardTitle>
                    <CardDescription className="text-slate-400">
                        React (Vite) frontend + FastAPI backend — for interactive OCR, scans, and settings in the browser.
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4 text-sm text-slate-300">
                    <div>
                        <h4 className="text-sky-400 font-medium mb-2">How it runs</h4>
                        <ul className="list-disc pl-5 space-y-1 text-slate-400">
                            <li>
                                <strong className="text-slate-300">Frontend</strong> —{' '}
                                <code className="text-slate-400">http://127.0.0.1:10858</code> (Vite dev server).
                            </li>
                            <li>
                                <strong className="text-slate-300">Backend API</strong> —{' '}
                                <code className="text-slate-400">127.0.0.1:10859</code> (FastAPI / Uvicorn). The UI proxies{' '}
                                <code className="text-slate-400">/api</code> and <code className="text-slate-400">/static</code>{' '}
                                to that port (see <code className="text-slate-400">web_sota/vite.config.ts</code>).
                            </li>
                            <li>
                                From repo root, <code className="text-slate-400">web_sota\start.ps1</code> clears those ports, syncs Python deps, and starts both processes. Same Python env as the MCP package (see repo <code className="text-slate-400">docs/INSTALL.md</code>).
                            </li>
                        </ul>
                    </div>
                    <div>
                        <h4 className="text-sky-400 font-medium mb-2">Pages in this app</h4>
                        <div className="overflow-x-auto rounded-lg border border-slate-800">
                            <table className="w-full text-left text-xs sm:text-sm border-collapse">
                                <thead>
                                    <tr className="border-b border-slate-800 bg-slate-950/80 text-slate-400">
                                        <th className="p-3 font-medium">Area</th>
                                        <th className="p-3 font-medium">Purpose</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-slate-800">
                                    <tr>
                                        <td className="p-3 font-mono text-slate-200">Dashboard</td>
                                        <td className="p-3 text-slate-400">Overview and entry points.</td>
                                    </tr>
                                    <tr>
                                        <td className="p-3 font-mono text-slate-200">Import</td>
                                        <td className="p-3 text-slate-400">Upload files; OCR runs in the background.</td>
                                    </tr>
                                    <tr>
                                        <td className="p-3 font-mono text-slate-200">Scanner</td>
                                        <td className="p-3 text-slate-400">WIA scanners on the host (Windows).</td>
                                    </tr>
                                    <tr>
                                        <td className="p-3 font-mono text-slate-200">Process</td>
                                        <td className="p-3 text-slate-400">Quality-focused pipelines and iterative optimization.</td>
                                    </tr>
                                    <tr>
                                        <td className="p-3 font-mono text-slate-200">Editor</td>
                                        <td className="p-3 text-slate-400">
                                            <strong className="text-slate-300">OCR text</strong> — latest result loads automatically; edit and export (e.g. JSON, CSV, XML). Job IDs are optional (advanced / Activity).
                                        </td>
                                    </tr>
                                    <tr>
                                        <td className="p-3 font-mono text-slate-200">Status</td>
                                        <td className="p-3 text-slate-400">Activity / job status for debugging.</td>
                                    </tr>
                                    <tr>
                                        <td className="p-3 font-mono text-slate-200">Chat</td>
                                        <td className="p-3 text-slate-400">Assistant-style UI when wired to the stack.</td>
                                    </tr>
                                    <tr>
                                        <td className="p-3 font-mono text-slate-200">Scan viewer</td>
                                        <td className="p-3 text-slate-400">Review scan output / viewer workflow.</td>
                                    </tr>
                                    <tr>
                                        <td className="p-3 font-mono text-slate-200">Settings</td>
                                        <td className="p-3 text-slate-400">
                                            Default OCR backend (stored in the browser), Mistral API key + base URL + test (stored in the{' '}
                                            <strong className="text-slate-300">backend process</strong> only), backend and scanner lists.
                                        </td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                    <p className="text-xs text-slate-500">
                        Tip: after upload or scan, open <strong className="text-slate-400">Editor</strong> — you don&apos;t need to copy internal job IDs for normal use.
                    </p>
                </CardContent>
            </Card>

            {/* —— MCP server —— */}
            <Card className="bg-slate-900/50 border-slate-800 backdrop-blur-xl">
                <CardHeader>
                    <CardTitle className="text-slate-100 flex items-center gap-2">
                        <Server className="w-5 h-5 text-violet-400" />
                        MCP server
                    </CardTitle>
                    <CardDescription className="text-slate-400">
                        FastMCP 3.1 server — stdio transport for agentic IDEs (Cursor, Claude Desktop, Windsurf, etc.). Same OCR engines as the web API, different entrypoint.
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4 text-sm text-slate-300">
                    <div>
                        <h4 className="text-violet-400 font-medium mb-2">What it is</h4>
                        <p className="text-slate-400 mb-2">
                            The MCP server exposes <strong className="text-slate-300">tools</strong>, <strong className="text-slate-300">resources</strong>, <strong className="text-slate-300">prompts</strong>, and (where the client supports it){' '}
                            <strong className="text-slate-300">sampling</strong> so an LLM can drive OCR, preprocessing, scanner ops, and batch workflows without using this browser UI.
                        </p>
                        <ul className="list-disc pl-5 space-y-1 text-slate-400">
                            <li>
                                <strong className="text-slate-300">Run:</strong>{' '}
                                <code className="text-slate-400">uv run ocr-mcp</code> or{' '}
                                <code className="text-slate-400">python -m ocr_mcp.server</code> from the project venv (see{' '}
                                <code className="text-slate-400">docs/INSTALL.md</code> for client JSON snippets).
                            </li>
                            <li>
                                <strong className="text-slate-300">Config:</strong> env vars such as{' '}
                                <code className="text-slate-400">MISTRAL_API_KEY</code>,{' '}
                                <code className="text-slate-400">MISTRAL_BASE_URL</code>,{' '}
                                <code className="text-slate-400">OCR_DEVICE</code>,{' '}
                                <code className="text-slate-400">OCR_CACHE_DIR</code>,{' '}
                                <code className="text-slate-400">OCR_AUTO_INSTALL_DEPS</code>,{' '}
                                <code className="text-slate-400">OCR_AUTO_BOOTSTRAP</code> (full matrix in repo docs).
                            </li>
                            <li>
                                <strong className="text-slate-300">Mistral note:</strong> the key you set under{' '}
                                <strong className="text-slate-300">Settings</strong> in the web UI applies to the FastAPI process only. The MCP server started by your IDE uses{' '}
                                <strong className="text-slate-300">environment variables</strong> unless you add a shared config layer — set{' '}
                                <code className="text-slate-400">MISTRAL_API_KEY</code> in the MCP client config if you use <code className="text-slate-400">mistral-ocr</code> from the agent.
                            </li>
                        </ul>
                    </div>
                    <div>
                        <h4 className="text-violet-400 font-medium mb-2">Portmanteau tools (high level)</h4>
                        <ul className="list-disc pl-5 space-y-1 text-slate-400">
                            <li>
                                <code className="text-slate-300">document_processing</code> — OCR, layout/analysis, quality checks (<code className="text-slate-400">operation</code> parameter).
                            </li>
                            <li>
                                <code className="text-slate-300">image_management</code> — preprocess, convert, image pipeline steps.
                            </li>
                            <li>
                                <code className="text-slate-300">scanner_operations</code> — list scanners, scan (WIA on Windows).
                            </li>
                            <li>
                                <code className="text-slate-300">workflow_management</code> — batches, pipelines, system-style workflow ops.
                            </li>
                            <li>
                                <code className="text-slate-300">agentic_document_workflow</code> — SEP-1577-style orchestration with sampling when the client supports it.
                            </li>
                        </ul>
                    </div>
                    <div>
                        <h4 className="text-violet-400 font-medium mb-2">Resources & prompts</h4>
                        <p className="text-slate-400">
                            Examples: <code className="text-slate-400">resource://ocr/logs</code>, <code className="text-slate-400">resource://ocr/capabilities</code>, skills/capability text for LLMs, and prompts for batch, scanner, quality, and agentic workflows. See{' '}
                            <code className="text-slate-400">src/ocr_mcp/server.py</code> and <code className="text-slate-400">docs/AI_FEATURES.md</code>.
                        </p>
                    </div>
                </CardContent>
            </Card>

            {/* —— OCR backends —— */}
            <Card className="bg-slate-900/50 border-slate-800 backdrop-blur-xl">
                <CardHeader>
                    <CardTitle className="text-slate-100 flex items-center gap-2">
                        <Cpu className="w-5 h-5 text-amber-400" />
                        OCR backends
                    </CardTitle>
                    <CardDescription className="text-slate-400">
                        Engines shared by the <strong>web API</strong> and the <strong>MCP server</strong>. Live status appears under{' '}
                        <strong>Settings</strong>. Choose per flow or set a browser default; MCP uses tool parameters / auto-routing.
                        The name <strong>florence-2</strong> in some tools may map to the current VL stack (<strong>paddleocr-vl</strong>) in this project.
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6 text-slate-300 text-sm">
                    <div className="overflow-x-auto rounded-lg border border-slate-800">
                        <table className="w-full text-left text-xs sm:text-sm border-collapse">
                            <thead>
                                <tr className="border-b border-slate-800 bg-slate-950/80 text-slate-400">
                                    <th className="p-3 font-medium">Backend</th>
                                    <th className="p-3 font-medium">Best for</th>
                                    <th className="p-3 font-medium">Trade-offs</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-800">
                                <tr>
                                    <td className="p-3 font-mono text-amber-200/90">paddleocr-vl</td>
                                    <td className="p-3">Documents, tables, formulas, charts, many languages; strong VL OCR.</td>
                                    <td className="p-3 text-slate-400">GPU + VRAM; install <strong>flash-attn</strong> on NVIDIA to avoid huge memory use. Needs torch/transformers stack.</td>
                                </tr>
                                <tr>
                                    <td className="p-3 font-mono text-amber-200/90">mistral-ocr</td>
                                    <td className="p-3">High-quality cloud OCR, structured output, mixed layouts.</td>
                                    <td className="p-3 text-slate-400">Requires API key (web <strong>Settings</strong> and/or <code className="text-slate-500">MISTRAL_API_KEY</code> for MCP); not offline; usage costs.</td>
                                </tr>
                                <tr>
                                    <td className="p-3 font-mono text-amber-200/90">deepseek-ocr2</td>
                                    <td className="p-3">Complex pages, newer DeepSeek pipeline (local HF model).</td>
                                    <td className="p-3 text-slate-400">Large download and GPU RAM; slower than tiny models.</td>
                                </tr>
                                <tr>
                                    <td className="p-3 font-mono text-amber-200/90">deepseek-ocr</td>
                                    <td className="p-3">Dense text, math, multilingual (local).</td>
                                    <td className="p-3 text-slate-400">Heavy model; setup like other HF backends.</td>
                                </tr>
                                <tr>
                                    <td className="p-3 font-mono text-amber-200/90">olmocr-2</td>
                                    <td className="p-3">Academic PDFs, math, multi-column (7B-class model).</td>
                                    <td className="p-3 text-slate-400">Very large; needs strong GPU for practical speed.</td>
                                </tr>
                                <tr>
                                    <td className="p-3 font-mono text-amber-200/90">dots-ocr</td>
                                    <td className="p-3">Tables, forms, structured documents.</td>
                                    <td className="p-3 text-slate-400">Less ideal for plain continuous text only.</td>
                                </tr>
                                <tr>
                                    <td className="p-3 font-mono text-amber-200/90">pp-ocrv5</td>
                                    <td className="p-3">Fast printed text, industrial / batch scenarios.</td>
                                    <td className="p-3 text-slate-400">Paddle CPU/CUDA wheel must match your machine; weak on handwriting vs specialized models.</td>
                                </tr>
                                <tr>
                                    <td className="p-3 font-mono text-amber-200/90">qwen-layered</td>
                                    <td className="p-3">Layered graphics, comics, mixed visual content.</td>
                                    <td className="p-3 text-slate-400">diffusers + GPU; not the default for simple scans.</td>
                                </tr>
                                <tr>
                                    <td className="p-3 font-mono text-amber-200/90">got-ocr</td>
                                    <td className="p-3">General OCR (GOT-OCR2 lineage), relatively lean HF model.</td>
                                    <td className="p-3 text-slate-400">Older stack vs newest VL options; still needs torch.</td>
                                </tr>
                                <tr>
                                    <td className="p-3 font-mono text-emerald-200/90">tesseract</td>
                                    <td className="p-3">Quick CPU OCR, many languages, no GPU.</td>
                                    <td className="p-3 text-slate-400">Weaker on complex layout/handwriting vs VL models; needs Tesseract binary (auto on Windows when possible).</td>
                                </tr>
                                <tr>
                                    <td className="p-3 font-mono text-emerald-200/90">easyocr</td>
                                    <td className="p-3">Handwriting and many languages; simple API.</td>
                                    <td className="p-3 text-slate-400">First run downloads models; slower; GPU optional via torch.</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                    <p className="text-xs text-slate-500">
                        Install matrices, env vars, and bootstrap: <code className="text-slate-400">docs/OCR_BACKEND_REQUIREMENTS.md</code>,{' '}
                        <code className="text-slate-400">docs/BACKEND_DEPS.md</code>, <code className="text-slate-400">docs/OCR_MODELS.md</code>.
                    </p>
                </CardContent>
            </Card>

            {/* —— Settings + repo docs —— */}
            <Card className="bg-slate-900/50 border-slate-800 backdrop-blur-xl">
                <CardHeader>
                    <CardTitle className="text-slate-100 flex items-center gap-2">
                        <FolderOpen className="w-5 h-5 text-emerald-400" />
                        Settings & further reading
                    </CardTitle>
                    <CardDescription className="text-slate-400">In-app options and repository documentation.</CardDescription>
                </CardHeader>
                <CardContent className="prose prose-invert prose-slate max-w-none text-sm">
                    <p className="text-slate-300">
                        <strong className="text-slate-200">Settings</strong> today: default OCR backend (browser localStorage), Mistral key + base URL + test connection (server memory), backend/scanner status.
                    </p>
                    <p className="text-slate-400 text-sm">
                        Roadmap ideas: Tesseract/EasyOCR language defaults, advanced paths (Poppler, Tesseract exe), refresh backends, privacy note for cloud backends, default export format.
                    </p>
                    <hr className="border-slate-800 my-4" />
                    <p className="text-slate-400 text-sm flex items-start gap-2">
                        <BookOpen className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                        <span>
                            Repo: <code className="text-slate-500">README.md</code> (overview), <code className="text-slate-500">docs/INSTALL.md</code> (web + MCP),{' '}
                            <code className="text-slate-500">docs/TECHNICAL.md</code> (architecture), <code className="text-slate-500">docs/AI_FEATURES.md</code> (sampling / agentic).
                        </span>
                    </p>
                </CardContent>
            </Card>
        </div>
    );
}
