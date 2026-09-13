import { ExternalLink, Github, Grid3X3, LayoutList, Loader2, Play, Rocket, Search, Star } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { API_BASE } from "@/api/client";

type FleetApp = {
  id: string;
  name: string;
  description: string;
  port: number;
  backend_port?: number;
  category: string;
  url: string | null;
  gh_url?: string;
  has_tauri?: boolean;
  has_tauri_installed?: boolean;
  last_commit?: string | null;
  repo_path?: string;
};

type Health = { port: number; alive: boolean; status_code?: number };

export function AppsPage() {
  const [apps, setApps] = useState<FleetApp[]>([]);
  const [fleetTotal, setFleetTotal] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [health, setHealth] = useState<Record<number, Health>>({});
  const [starting, setStarting] = useState<Record<string, boolean>>({});
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState<string>("all");
  const [sort, setSort] = useState<"name" | "port" | "recent">("port");
  const [view, setView] = useState<"cards" | "list">("cards");

  useEffect(() => {
    fetch(`${API_BASE}/api/apps`)
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then((j) => {
        const list = (j.apps as FleetApp[]) ?? [];
        setApps(list);
        setFleetTotal(j.fleet_total ?? 0);
        list.forEach((a) => {
          fetch(`${API_BASE}/api/apps/health?port=${a.port}`)
            .then((r) => r.json())
            .then((h) => setHealth((prev) => ({ ...prev, [a.port]: h })))
            .catch(() =>
              setHealth((prev) => ({
                ...prev,
                [a.port]: { port: a.port, alive: false },
              })),
            );
        });
      })
      .catch((e) => setError(e instanceof Error ? e.message : "load failed"));
  }, []);

  const categories = useMemo(() => {
    const cats = new Set(apps.map((a) => a.category).filter(Boolean));
    return ["all", ...Array.from(cats).sort()];
  }, [apps]);

  const filtered = useMemo(() => {
    let out = apps.filter((a) => {
      if (category !== "all" && a.category !== category) return false;
      if (query) {
        const q = query.toLowerCase();
        if (
          !a.id.toLowerCase().includes(q) &&
          !a.name.toLowerCase().includes(q) &&
          !a.description.toLowerCase().includes(q)
        )
          return false;
      }
      return true;
    });
    out = [...out].sort((a, b) => {
      if (sort === "name") return a.name.localeCompare(b.name);
      if (sort === "port") return a.port - b.port;
      // recent: last_commit desc (ISO string), fallback to name
      const ta = a.last_commit ? Date.parse(a.last_commit) : 0;
      const tb = b.last_commit ? Date.parse(b.last_commit) : 0;
      if (tb !== ta) return tb - ta;
      return a.name.localeCompare(b.name);
    });
    return out;
  }, [apps, query, category, sort]);

  const openApp = async (app: FleetApp) => {
    const h = health[app.port];
    if (h?.alive) {
      window.open(app.url ?? `http://127.0.0.1:${app.port}`, "_blank");
      return;
    }
    setStarting((s) => ({ ...s, [app.id]: true }));
    try {
      const r = await fetch(`${API_BASE}/api/apps/ensure`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id: app.id, port: app.port }),
      });
      const j = await r.json();
      if (j.alive || j.status === "already_running" || j.status === "brought_to_foreground") {
        if (j.status === "brought_to_foreground") {
          if (!j.alive) {
            setError(`${app.id}: Tauri window brought to front — no web UI on :${app.port}`);
          } else {
            setTimeout(() => window.open(j.url ?? app.url ?? `http://127.0.0.1:${app.port}`, "_blank"), 300);
          }
        } else {
          window.open(j.url ?? app.url ?? `http://127.0.0.1:${app.port}`, "_blank");
        }
        const hr = await fetch(`${API_BASE}/api/apps/health?port=${app.port}`)
          .then((x) => x.json())
          .catch(() => null);
        if (hr) setHealth((prev) => ({ ...prev, [app.port]: hr }));
      } else if (j.status === "started" || j.status === "start_initiated" || j.status === "tauri_started") {
        for (let i = 0; i < 15; i++) {
          await new Promise((res) => setTimeout(res, 1000));
          const hr = await fetch(`${API_BASE}/api/apps/health?port=${app.port}`)
            .then((x) => x.json())
            .catch(() => null);
          if (hr) {
            setHealth((prev) => ({ ...prev, [app.port]: hr }));
            if (hr.alive) {
              window.open(hr.health_url ?? app.url ?? `http://127.0.0.1:${app.port}`, "_blank");
              break;
            }
          }
        }
      } else {
        const headless = j.error && /no.*start|headless|no web/i.test(String(j.error));
        if (headless || (app.has_tauri && !app.url)) {
          setError(
            `${app.id}: ${j.error ?? `No web UI — headless MCP/Tauri app. Use its winapp via Starts or: uv run ${app.id}`}`,
          );
        } else {
          window.open(app.url ?? `http://127.0.0.1:${app.port}`, "_blank");
          if (j.error) setError(`${app.id}: ${j.error}`);
        }
      }
    } catch (e) {
      if (app.has_tauri) {
        setError(`${app.id}: ${e instanceof Error ? e.message : String(e)} — no web UI, try Tauri winapp or start.ps1`);
      } else {
        window.open(app.url ?? `http://127.0.0.1:${app.port}`, "_blank");
        setError(e instanceof Error ? e.message : String(e));
      }
    } finally {
      setStarting((s) => ({ ...s, [app.id]: false }));
    }
  };

  return (
    <div className="space-y-6" data-testid="apps-page">
      {/* Hero */}
      <div
        className="rounded-2xl border border-border bg-gradient-to-br from-card via-card to-black/20 p-6"
        data-testid="apps-hero"
      >
        <div className="flex items-start gap-3">
          <div className="w-9 h-9 rounded-xl bg-gh-green/10 border border-gh-green/20 flex items-center justify-center shrink-0">
            <Grid3X3 className="w-4 h-4 text-gh-green" />
          </div>
          <div className="space-y-2">
            <h1 className="text-2xl font-bold tracking-tight">Fleet apps — start or switch</h1>
            <p className="text-sm text-muted-foreground leading-relaxed max-w-[70ch]">
              All installed <span className="font-mono text-xs">sandraschi</span> repos with a webapp (from{" "}
              <span className="font-mono text-xs">fleet-registry.json</span> +{" "}
              <span className="font-mono text-xs">WEBAPP_PORTS.md</span>). Click a card to check{" "}
              <span className="font-mono text-xs">:{`{port}`}/health</span> first. If it is up, we open it; if a Tauri
              winapp is already running we bring it to the foreground; otherwise we start it via{" "}
              <span className="font-mono text-xs">mcd starts\{`{id}`}-start.bat</span> →{" "}
              <span className="font-mono text-xs">repo\start.ps1</span> → Tauri exe and then open.
            </p>
            <div className="flex flex-wrap gap-2 text-xs font-mono">
              <span className="px-2 py-1 rounded bg-white/5 border border-white/10">{fleetTotal} repos total</span>
              <span className="px-2 py-1 rounded bg-gh-green/10 border border-gh-green/20 text-gh-green">
                {apps.length} with ports
              </span>
              <span className="px-2 py-1 rounded bg-white/5 border border-white/10">{filtered.length} shown</span>
            </div>
          </div>
        </div>
      </div>

      {/* Controls */}
      <div className="flex flex-col lg:flex-row gap-3 lg:items-center justify-between">
        <div className="flex flex-1 flex-wrap gap-2">
          <div className="relative flex-1 min-w-[200px] max-w-sm">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <input
              data-testid="apps-filter"
              placeholder="Filter by name or description..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="w-full pl-9 pr-3 py-2 rounded-lg bg-card border border-border text-sm focus:outline-none focus:ring-1 focus:ring-gh-green/30"
            />
          </div>
          <select
            data-testid="apps-category"
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            className="px-3 py-2 rounded-lg bg-card border border-border text-sm"
          >
            {categories.map((c) => (
              <option key={c} value={c}>
                {c === "all" ? "All categories" : c}
              </option>
            ))}
          </select>
          <select
            data-testid="apps-sort"
            value={sort}
            onChange={(e) => setSort(e.target.value as never)}
            className="px-3 py-2 rounded-lg bg-card border border-border text-sm"
          >
            <option value="port">Sort by port</option>
            <option value="name">Sort by name</option>
            <option value="recent">Sort by recent commit</option>
          </select>
        </div>
        <div className="flex items-center gap-1 p-1 rounded-lg bg-black/20 border border-white/5 self-start">
          <button
            type="button"
            data-testid="apps-view-cards"
            onClick={() => setView("cards")}
            className={`p-2 rounded-md ${view === "cards" ? "bg-white text-black" : "text-muted-foreground hover:text-foreground"}`}
            title="Card view"
          >
            <Grid3X3 className="w-4 h-4" />
          </button>
          <button
            type="button"
            data-testid="apps-view-list"
            onClick={() => setView("list")}
            className={`p-2 rounded-md ${view === "list" ? "bg-white text-black" : "text-muted-foreground hover:text-foreground"}`}
            title="List view"
          >
            <LayoutList className="w-4 h-4" />
          </button>
        </div>
      </div>

      {error && <p className="text-sm text-red-400">{error}</p>}

      {/* Cards / List */}
      {view === "cards" ? (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {filtered.map((app) => {
            const h = health[app.port];
            const alive = h?.alive;
            const isStarting = starting[app.id];
            return (
              <div
                key={app.id}
                className="rounded-xl border border-border bg-card/40 p-4 hover:border-gh-green/20 hover:bg-white/[0.02] transition-colors flex flex-col"
                data-testid={`app-card-${app.id}`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0">
                    <div className="font-medium text-sm flex items-center gap-2">
                      <span
                        className={`w-2 h-2 rounded-full shrink-0 ${alive ? "bg-gh-green shadow-[0_0_8px_rgba(34,197,94,0.5)]" : alive === false ? "bg-red-500/60" : "bg-gray-500 animate-pulse"}`}
                      />
                      <span className="truncate">{app.name}</span>
                    </div>
                    <div className="flex flex-wrap gap-1 mt-1">
                      <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-white/5 border border-white/10">
                        {app.category}
                      </span>
                      <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-gh-green/10 border border-gh-green/20 text-gh-green">
                        :{app.port}
                      </span>
                      {app.has_tauri && (
                        <span
                          className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-amber-500/10 border border-amber-500/20 text-amber-400"
                          title={app.has_tauri_installed ? "Tauri winapp installed" : "Tauri capable"}
                        >
                          Tauri{app.has_tauri_installed ? " • installed" : ""}
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-1 shrink-0">
                    <a
                      href={app.gh_url}
                      target="_blank"
                      rel="noreferrer"
                      title="GitHub repo"
                      className="p-1.5 rounded-md hover:bg-white/10 text-muted-foreground hover:text-foreground"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <Github className="w-3.5 h-3.5" />
                    </a>
                  </div>
                </div>
                <p className="text-xs text-muted-foreground mt-2 line-clamp-3 flex-1">{app.description}</p>
                {app.last_commit && (
                  <p className="text-[10px] font-mono text-muted-foreground/60 mt-1">
                    last commit {new Date(app.last_commit).toLocaleDateString()}
                  </p>
                )}
                <div className="flex items-center gap-2 mt-3">
                  <button
                    type="button"
                    onClick={() => openApp(app)}
                    disabled={isStarting}
                    className={`flex-1 inline-flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-sm font-semibold transition-colors ${alive ? "bg-white text-black hover:bg-zinc-200" : "bg-amber-500 text-black hover:bg-amber-400"} disabled:opacity-60`}
                    data-testid={`app-open-${app.id}`}
                  >
                    {isStarting ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : alive ? (
                      <ExternalLink className="w-4 h-4" />
                    ) : (
                      <Play className="w-4 h-4" />
                    )}
                    {isStarting ? "Starting…" : alive ? "Open" : "Start"}
                  </button>
                  <span
                    className={`text-[10px] font-mono px-2 py-1 rounded border ${alive ? "bg-gh-green/10 border-gh-green/20 text-gh-green" : "bg-white/5 border-white/10 text-muted-foreground"}`}
                  >
                    {alive ? "running" : alive === false ? "stopped" : "checking…"}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="rounded-xl border border-border bg-card/40 overflow-hidden">
          <div className="divide-y divide-white/5">
            <div className="hidden sm:grid grid-cols-[1fr_90px_80px_120px_100px] gap-2 px-4 py-2 text-[10px] font-bold uppercase tracking-widest text-muted-foreground/60">
              <span>Name</span>
              <span>Port</span>
              <span>Category</span>
              <span>Updated</span>
              <span className="text-right">Action</span>
            </div>
            {filtered.map((app) => {
              const h = health[app.port];
              const alive = h?.alive;
              const isStarting = starting[app.id];
              return (
                <div
                  key={app.id}
                  className="grid sm:grid-cols-[1fr_90px_80px_120px_100px] gap-2 px-4 py-3 hover:bg-white/[0.02] items-center"
                >
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <span className={`w-2 h-2 rounded-full ${alive ? "bg-gh-green" : "bg-red-500/60"}`} />
                      <span className="text-sm font-medium truncate">{app.name}</span>
                      {app.has_tauri && <Star className="w-3 h-3 text-amber-400" />}
                    </div>
                    <p className="text-xs text-muted-foreground truncate hidden sm:block">{app.description}</p>
                  </div>
                  <span className="text-xs font-mono text-gh-green">:{app.port}</span>
                  <span className="text-xs font-mono">{app.category}</span>
                  <span className="text-xs font-mono text-muted-foreground">
                    {app.last_commit ? new Date(app.last_commit).toLocaleDateString() : "—"}
                  </span>
                  <div className="flex items-center justify-end gap-2">
                    <a href={app.gh_url} target="_blank" rel="noreferrer" className="p-1.5 rounded hover:bg-white/10">
                      <Github className="w-3.5 h-3.5" />
                    </a>
                    <button
                      type="button"
                      onClick={() => openApp(app)}
                      disabled={isStarting}
                      className={`px-3 py-1.5 rounded-lg text-xs font-semibold ${alive ? "bg-white text-black" : "bg-amber-500 text-black"} disabled:opacity-60`}
                    >
                      {isStarting ? "..." : alive ? "Open" : "Start"}
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {filtered.length === 0 && <p className="text-sm text-muted-foreground text-center py-8">No apps match filter.</p>}

      <div className="rounded-lg border border-dashed border-border bg-black/20 p-4 flex items-start gap-3">
        <Rocket className="w-4 h-4 text-muted-foreground mt-0.5" />
        <div className="text-xs text-muted-foreground leading-relaxed">
          <span className="font-semibold text-foreground">Fleet standard:</span> every{" "}
          <span className="font-mono">Apps</span> page checks <span className="font-mono">:{`{port}`}/health</span>{" "}
          first; if a Tauri winapp is already running we bring it to front, otherwise we launch{" "}
          <span className="font-mono">mcd starts\{`{id}`}-start.bat</span> →{" "}
          <span className="font-mono">repo\start.ps1</span> → Tauri exe and then open. Descriptions prefer{" "}
          <span className="font-mono">pyproject.toml description</span> (plain) with{" "}
          <span className="font-mono">gh repo</span> fallback — optimize there.
        </div>
      </div>
    </div>
  );
}
