/* AI settings page — template (SETTINGS_LLM.md rules enforced).
 *
 * A complete page holding ALL AI-related settings, separate from the repo's own
 * Settings page. Additive adoption only: add a route + nav entry, never edit or
 * delete the repo's existing settings (see header note in ActiveLlmCard.tsx).
 *
 * Composition:
 *   - LlmOnboarding  (first-run provider/key setup; silent when onboarded)
 *   - ActiveLlmCard  (selection, save=VRAM-switch, kick-out, telemetry)
 *   - LlmProviderCards (per-provider detection + cloud API key inputs)
 *
 * Adaptation: fix the three relative imports below to your tree.
 * Required backend: see ActiveLlmCard.tsx header (same endpoint list) plus
 *   the key endpoints LlmProviderCards already uses
 *   (POST /api/settings/llm with api_key, DELETE /api/settings/llm/key).
 *
 * Reference implementation: arxiv-mcp web_sota/src/pages/AiSettingsPage.tsx.
 */

import { useCallback, useEffect, useState } from "react";
import { ActiveLlmCard } from "./ActiveLlmCard";
import { LlmOnboarding } from "./LlmOnboarding";
import { LlmProviderCards } from "./LlmProviderCards";
import { fetchLlmSettings, fetchProviders, loadSelection, type ProviderInfo } from "./lib-llm";

export function AiSettingsPage() {
  const [providers, setProviders] = useState<ProviderInfo[]>([]);
  const [probing, setProbing] = useState(true);
  const [selected, setSelected] = useState("ollama");

  const refreshProviders = useCallback(async () => {
    try {
      const pv = await fetchProviders();
      setProviders(pv.providers);
    } catch {
      /* keep previous list */
    }
  }, []);

  useEffect(() => {
    (async () => {
      await refreshProviders();
      const prev = loadSelection();
      if (prev.provider) setSelected(prev.provider);
      try {
        const s = await fetchLlmSettings();
        if (s.provider) setSelected(s.provider);
      } catch {
        /* backend truth unavailable: local mirror stands */
      }
      setProbing(false);
    })();
  }, [refreshProviders]);

  async function handleCardsChanged() {
    await refreshProviders();
  }

  return (
    <div className="space-y-4" data-testid="ai-settings-page">
      <LlmOnboarding mode="full" />
      <ActiveLlmCard />
      <LlmProviderCards providers={providers} probing={probing} selected={selected} onChanged={handleCardsChanged} />
    </div>
  );
}
