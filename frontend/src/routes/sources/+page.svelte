<script lang="ts">
  import { onMount } from 'svelte';
  import { api, type LibraryRoot } from '$lib/api';

  let roots = $state<LibraryRoot[]>([]);
  let error = $state<string | null>(null);
  let loaded = $state(false);

  onMount(async () => {
    try {
      roots = await api<LibraryRoot[]>('/sources');
    } catch (e) {
      error = e instanceof Error ? e.message : String(e);
    } finally {
      loaded = true;
    }
  });
</script>

<h1 class="mb-6 text-2xl font-semibold tracking-tight">Sources</h1>

{#if error}
  <div class="rounded border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div>
{:else if !loaded}
  <p class="text-sm text-zinc-500">Loading…</p>
{:else if roots.length === 0}
  <div class="rounded-lg border border-dashed border-zinc-300 bg-white p-12 text-center text-sm text-zinc-600">
    No library roots configured yet.
  </div>
{:else}
  <ul class="space-y-2">
    {#each roots as root}
      <li class="flex items-center justify-between rounded border border-zinc-200 bg-white p-3 text-sm">
        <span><span class="font-mono text-xs text-zinc-500">{root.kind}</span> {root.path}</span>
        <span class="text-xs text-zinc-500">{root.enabled ? 'enabled' : 'disabled'}</span>
      </li>
    {/each}
  </ul>
{/if}
