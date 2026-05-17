<script lang="ts">
  import { onMount } from 'svelte';
  import { api, type Stats } from '$lib/api';

  let stats = $state<Stats | null>(null);
  let error = $state<string | null>(null);

  onMount(async () => {
    try {
      stats = await api<Stats>('/stats');
    } catch (e) {
      error = e instanceof Error ? e.message : String(e);
    }
  });
</script>

<h1 class="mb-6 text-2xl font-semibold tracking-tight">Dashboard</h1>

{#if error}
  <div class="rounded border border-red-200 bg-red-50 p-3 text-sm text-red-700">
    Failed to load stats: {error}
  </div>
{:else if !stats}
  <p class="text-sm text-zinc-500">Loading…</p>
{:else}
  <div class="grid grid-cols-2 gap-3 sm:grid-cols-4">
    <div class="rounded-lg border border-zinc-200 bg-white p-4">
      <div class="text-xs uppercase tracking-wide text-zinc-500">Works</div>
      <div class="mt-1 text-2xl font-semibold">{stats.works}</div>
    </div>
    <div class="rounded-lg border border-zinc-200 bg-white p-4">
      <div class="text-xs uppercase tracking-wide text-zinc-500">Assets</div>
      <div class="mt-1 text-2xl font-semibold">{stats.assets}</div>
    </div>
    <div class="rounded-lg border border-zinc-200 bg-white p-4">
      <div class="text-xs uppercase tracking-wide text-zinc-500">Tags</div>
      <div class="mt-1 text-2xl font-semibold">{stats.tags}</div>
    </div>
    <div class="rounded-lg border border-zinc-200 bg-white p-4">
      <div class="text-xs uppercase tracking-wide text-zinc-500">Needs review</div>
      <div class="mt-1 text-2xl font-semibold">{stats.review_queue}</div>
    </div>
  </div>

  <div class="mt-8 rounded-lg border border-zinc-200 bg-white p-6 text-sm text-zinc-600">
    <p class="font-medium text-zinc-900">v0.1 scaffold</p>
    <p class="mt-2">
      Schema and UI shell are in place. Adapters (filesystem, Audiobookshelf, Calibre)
      and the matcher are stubbed and will be wired up next.
    </p>
  </div>
{/if}
