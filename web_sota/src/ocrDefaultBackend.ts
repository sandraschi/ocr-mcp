/** localStorage key for default OCR backend (shared by Scanner, Scan Viewer, Settings). */
export const OCR_DEFAULT_BACKEND_KEY = "ocr_default_backend";

export function loadOcrDefaultBackend(): string {
  if (typeof window === "undefined") return "auto";
  return window.localStorage.getItem(OCR_DEFAULT_BACKEND_KEY) || "auto";
}

export function saveOcrDefaultBackend(value: string): void {
  window.localStorage.setItem(OCR_DEFAULT_BACKEND_KEY, value);
}
