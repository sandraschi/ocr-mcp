import { Activity, Archive, Book, Bot, Brain, LayoutGrid, Mail, MessageSquare, MonitorPlay, Scan } from "lucide-react";

export interface AppEntry {
  id: string;
  label: string;
  description: string;
  port: number;
  tags: string[];
  alive: boolean;
  url?: string;
}

const iconMap: Record<string, any> = {
  "fleet-dashboard": LayoutGrid,
  "advanced-memory": Brain,
  "local-llm": MessageSquare,
  "calibre-mcp": Book,
  "email-mcp": Mail,
  "plex-mcp": MonitorPlay,
  "osc-mcp": Activity,
  robotics: Bot,
  "obs-mcp": MonitorPlay,
  "ocr-interface": Scan,
  winrar: Archive,
};

export function getAppIcon(id: string): any {
  return iconMap[id] || LayoutGrid;
}

export async function fetchFleetApps(): Promise<AppEntry[]> {
  try {
    const res = await fetch("/api/fleet/apps");
    if (!res.ok) return [];
    const data = await res.json();
    return data.apps || [];
  } catch {
    return [];
  }
}
