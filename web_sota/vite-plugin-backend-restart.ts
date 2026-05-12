import { spawn } from "node:child_process";
import path from "node:path";
import type { Plugin } from "vite";

const BACKEND_PORT = 10859;
const PROJECT_ROOT = path.resolve(__dirname, "..");

let backendProcess: ReturnType<typeof spawn> | null = null;

export function backendRestartPlugin(): Plugin {
  return {
    name: "ocr-mcp-backend-restart",
    configureServer(server) {
      // Add /api/restart endpoint to Vite dev server (works when backend is dead)
      server.middlewares.use("/api/restart", (req, res) => {
        if (req.method !== "POST") {
          res.statusCode = 405;
          res.end(JSON.stringify({ error: "Method not allowed" }));
          return;
        }

        // Kill existing backend if running
        if (backendProcess) {
          try { backendProcess.kill(); } catch {}
          backendProcess = null;
        }

        // The POST /api/restart on backend:10859 also handles spawning,
        // but if the backend is dead this Vite plugin catches it and respawns.
        const child = spawn(
          "uv",
          ["run", "uvicorn", "backend.app:app", "--host", "127.0.0.1", "--port", String(BACKEND_PORT)],
          {
            cwd: PROJECT_ROOT,
            stdio: "ignore",
            detached: false,
            shell: true,
          },
        );

        backendProcess = child;
        child.unref();

        child.on("error", (err) => {
          console.error("Backend spawn error:", err.message);
        });

        // Give backend a moment, then proxy through
        setTimeout(async () => {
          // Try to reach the backend
          for (let i = 0; i < 15; i++) {
            try {
              const resp = await fetch(`http://127.0.0.1:${BACKEND_PORT}/api/health`);
              if (resp.ok) {
                res.setHeader("Content-Type", "application/json");
                res.end(JSON.stringify({ success: true, message: "Backend restarted" }));
                return;
              }
            } catch {}
            await new Promise((r) => setTimeout(r, 1000));
          }
          res.setHeader("Content-Type", "application/json");
          res.end(JSON.stringify({ success: true, message: "Backend starting (may take a moment)" }));
        }, 100);
      });
    },
  };
}
