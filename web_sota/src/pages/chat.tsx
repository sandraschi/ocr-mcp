import { Bot, Download, Eraser, Send, User } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";

const HISTORY_KEY = "ocr-mcp-chat-history";
const PERSONALITY_KEY = "ocr-mcp-chat-personality";
const MAX_HISTORY = 100;

const PERSONALITIES: Record<string, string> = {
  "OCR Specialist":
    "You are an OCR specialist. Extract text accurately from images. Describe any formatting, tables, or layouts you detect. Be precise about character recognition.",
  "Document Analyst":
    "You are a document analyst. Analyze document structure, identify sections, headers, tables, and figures. Provide structured output describing the document architecture.",
  "Quick Summarizer": "Keep responses to 2-3 sentences. Focus on key facts.",
  Custom: "Custom prompt \u2014 editable below.",
};

const EXAMPLE_PROMPTS = [
  {
    group: "Images",
    prompts: [
      "Extract text from this scanned document",
      "Identify tables in the image and format as CSV",
      "Describe the layout and structure of this page",
    ],
  },
  {
    group: "Text",
    prompts: [
      "Convert this image to Markdown format",
      "Extract handwritten text from the photo",
      "Find all numbers and dates in the document",
    ],
  },
  {
    group: "Format",
    prompts: [
      "OCR this invoice and extract key fields",
      "Recognize text from a screenshot",
      "Process a multi-page document",
    ],
  },
];

export function Chat() {
  const [personality, setPersonality] = useState(() => localStorage.getItem(PERSONALITY_KEY) || "OCR Specialist");
  const [messages, setMessages] = useState<{ role: "user" | "assistant"; content: string }[]>(() => {
    try {
      return JSON.parse(localStorage.getItem(HISTORY_KEY) || "[]");
    } catch {
      return [];
    }
  });
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    localStorage.setItem(HISTORY_KEY, JSON.stringify(messages));
  }, [messages]);
  useEffect(() => {
    localStorage.setItem(PERSONALITY_KEY, personality);
  }, [personality]);
  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const send = useCallback(async () => {
    const text = input.trim();
    if (!text || sending) return;
    setInput("");
    const userMsg = { role: "user" as const, content: text };
    setMessages((prev) => {
      const next = [...prev, userMsg];
      return next.length > MAX_HISTORY ? next.slice(-MAX_HISTORY) : next;
    });
    setSending(true);
    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text, personality }),
      });
      const data = await res.json();
      setMessages((prev) => [
        ...prev,
        { role: "assistant" as const, content: data.response || data.content || "No response" },
      ]);
    } catch (e) {
      setMessages((prev) => [...prev, { role: "assistant", content: `Error: ${(e as Error).message}` }]);
    }
    setSending(false);
  }, [input, sending, personality]);

  const exportChat = () => {
    const text = messages.map((m) => `[${m.role.toUpperCase()}] ${m.content}`).join("\n\n");
    const blob = new Blob([text], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "ocr-mcp-chat.txt";
    a.click();
    URL.revokeObjectURL(url);
  };

  const clearChat = () => {
    setMessages([]);
  };

  return (
    <div data-testid="chat-page" className="flex h-[calc(100vh-8rem)] flex-col space-y-4">
      <div data-testid="chat-controls" className="flex items-center justify-between flex-wrap gap-2">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white">Chat</h2>
          <p className="text-slate-400">OCR MCP \u2014 an OCR server for extracting text from images</p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-500 bg-slate-800 px-2 py-1 rounded">skill:ocr-expert</span>
          <select
            data-testid="personality-select"
            className="bg-slate-900 border border-slate-700 rounded px-2 py-1 text-xs text-slate-200"
            value={personality}
            onChange={(e) => setPersonality(e.target.value)}
          >
            {Object.keys(PERSONALITIES).map((p) => (
              <option key={p} value={p}>
                {p}
              </option>
            ))}
          </select>
          <button
            data-testid="chat-export"
            onClick={exportChat}
            disabled={messages.length === 0}
            className="p-1.5 rounded hover:bg-slate-800 text-slate-400 disabled:opacity-30"
            title="Export"
          >
            <Download className="h-4 w-4" />
          </button>
          <button
            data-testid="chat-clear"
            onClick={clearChat}
            disabled={messages.length === 0}
            className="p-1.5 rounded hover:bg-slate-800 text-slate-400 disabled:opacity-30"
            title="Clear"
          >
            <Eraser className="h-4 w-4" />
          </button>
        </div>
      </div>

      <div data-testid="chat-messages" className="flex-1 overflow-y-auto space-y-4">
        {messages.length === 0 ? (
          <div className="text-center text-slate-500 py-8 text-sm">Start a conversation with the OCR assistant.</div>
        ) : (
          messages.map((msg, i) => (
            <div key={i} className="flex gap-3">
              <div
                className={`h-8 w-8 rounded-full flex items-center justify-center border shrink-0 ${msg.role === "user" ? "bg-slate-800 border-slate-700" : "bg-blue-900/20 border-blue-800"}`}
              >
                {msg.role === "user" ? (
                  <User className="h-4 w-4 text-slate-400" />
                ) : (
                  <Bot className="h-4 w-4 text-blue-400" />
                )}
              </div>
              <div className="flex-1 space-y-1">
                <span className={`text-sm font-medium ${msg.role === "user" ? "text-slate-200" : "text-blue-400"}`}>
                  {msg.role === "user" ? "You" : "Assistant"}
                </span>
                <div
                  className={`text-sm p-3 rounded-md border whitespace-pre-wrap ${msg.role === "user" ? "text-slate-300 bg-slate-900/50 border-slate-800" : "text-slate-300 bg-blue-950/10 border-blue-900/30"}`}
                >
                  {msg.content}
                </div>
              </div>
            </div>
          ))
        )}
        {sending && (
          <div className="flex items-center gap-2 text-sm text-slate-500">
            <div className="h-4 w-4 animate-spin rounded-full border-2 border-slate-500 border-t-transparent" />
            Thinking...
          </div>
        )}
        <div ref={scrollRef} />
      </div>

      <div data-testid="example-prompts" className="flex flex-wrap gap-2">
        {EXAMPLE_PROMPTS.map((group) => (
          <div key={group.group} className="flex flex-wrap items-center gap-1">
            <span className="text-xs text-slate-500 mr-1">{group.group}:</span>
            {group.prompts.map((p) => (
              <button
                key={p}
                onClick={() => setInput(p)}
                className="text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 px-2 py-1 rounded"
              >
                {p}
              </button>
            ))}
          </div>
        ))}
      </div>

      <div className="flex gap-2">
        <input
          data-testid="chat-input"
          className="flex-1 bg-slate-950 border border-slate-800 rounded-md px-4 py-2 text-sm text-white focus:outline-none focus:ring-1 focus:ring-blue-500"
          placeholder="Ask about OCR..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              send();
            }
          }}
        />
        <button
          data-testid="chat-send"
          onClick={send}
          disabled={sending || !input.trim()}
          className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white px-4 py-2 rounded-md"
        >
          {sending ? (
            <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
          ) : (
            <Send className="h-4 w-4" />
          )}
        </button>
      </div>
    </div>
  );
}
