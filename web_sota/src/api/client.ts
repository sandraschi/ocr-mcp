// Minimal same-origin API client (ocr-mcp convention).
//
// Every page in this repo calls fetch("/api/...") straight through the Vite
// dev proxy (vite.config.ts: /api -> backend :10859). This module gives the
// vendored fleet LLM surfaces (components/llm/*) the apiGet/apiPost/apiDelete
// helpers their templates import from "@/api/client", without introducing a
// base-URL concept this repo does not use. API_BASE is "" by construction.

export const API_BASE = "";

async function parseBody(res: Response): Promise<unknown> {
  const text = await res.text();
  if (!text) return {};
  try {
    return JSON.parse(text);
  } catch {
    return { message: text.slice(0, 300) };
  }
}

function httpError(method: string, path: string, res: Response, body: unknown): Error {
  const detail =
    typeof body === "object" && body !== null
      ? ((body as Record<string, unknown>).detail ??
        (body as Record<string, unknown>).error ??
        (body as Record<string, unknown>).message)
      : null;
  const suffix = typeof detail === "string" && detail ? `: ${detail}` : "";
  return new Error(`${method} ${path} -> HTTP ${res.status}${suffix}`);
}

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers: { "Content-Type": "application/json" },
    ...(body === undefined ? {} : { body: JSON.stringify(body) }),
  });
  const data = await parseBody(res);
  if (!res.ok) throw httpError(method, path, res, data);
  return data as T;
}

export function apiGet<T>(path: string): Promise<T> {
  return request<T>("GET", path);
}

export function apiPost<T>(path: string, body?: unknown): Promise<T> {
  return request<T>("POST", path, body);
}

export function apiDelete<T>(path: string): Promise<T> {
  return request<T>("DELETE", path);
}
