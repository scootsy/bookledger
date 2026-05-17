<script lang="ts">
  import { onDestroy, onMount } from 'svelte';
  import { api, type ScanStatus, type Stats } from '$lib/api';

  let stats = $state<Stats | null>(null);
  let scan = $state<ScanStatus | null>(null);
  let error = $state<string | null>(null);
  let polling: ReturnType<typeof setInterval> | null = null;

  async function refresh() {
    try {
      const [s, sc] = await Promise.all([api<Stats>('/stats'), api<ScanStatus>('/scan/status')]);
      stats = s;
      scan = sc;
      error = null;
    } catch (e) {
      error = e instanceof Error ? e.message : String(e);
    }
  }

  async function runScan() {
    error = null;
    try {
      await api('/scan/run', { method: 'POST' });
      await refresh();
    } catch (e) {
      error = e instanceof Error ? e.message : String(e);
    }
  }

  onMount(async () => {
    await refresh();
    polling = setInterval(refresh, 2000);
  });

  onDestroy(() => {
    if (polling) clearInterval(polling);
  });
</script>

<div class="mb-6 flex items-center justify-between">
  <h1 class="text-2xl font-semibold tracking-tight">Dashboard</h1>
  <button
    onclick={runScan}
    disabled={scan?.running}
    class="rounded bg-zinc-900 px-4 py-1.5 text-sm font-medium text-white shadow-sm hover:bg-zinc-800 disabled:cursor-not-allowed disabled:opacity-50"
  >
    {scan?.running ? 'Scanning…' : 'Scan all sources'}
  </button>
</div>

{#if error}
  <div class="mb-4 rounded border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div>
{/if}

{#if stats}
  <div class="grid grid-cols-2 gap-3 sm:grid-cols-4">
    <a
      href="/library"
      class="rounded-lg border border-zinc-200 bg-white p-4 hover:border-zinc-400"
    >
      <div class="text-xs uppercase tracking-wide text-zinc-500">Works</div>
      <div class="mt-1 text-2xl font-semibold">{stats.works}</div>
    </a>
    <div class="rounded-lg border border-zinc-200 bg-white p-4">
      <div class="text-xs uppercase tracking-wide text-zinc-500">Assets</div>
      <div class="mt-1 text-2xl font-semibold">{stats.assets}</div>
    </div>
    <a href="/tags" class="rounded-lg border border-zinc-200 bg-white p-4 hover:border-zinc-400">
      <div class="text-xs uppercase tracking-wide text-zinc-500">Tags</div>
      <div class="mt-1 text-2xl font-semibold">{stats.tags}</div>
    </a>
    <a
      href="/review"
      class="rounded-lg border border-zinc-200 bg-white p-4 hover:border-zinc-400"
    >
      <div class="text-xs uppercase tracking-wide text-zinc-500">Needs review</div>
      <div class="mt-1 text-2xl font-semibold">{stats.review_queue}</div>
    </a>
  </div>
{/if}

{#if scan}
  <div class="mt-8 rounded-lg border border-zinc-200 bg-white p-4">
    <div class="flex items-center justify-between">
      <div class="text-sm font-medium">Scan status</div>
      {#if scan.running}
        <span class="inline-flex items-center gap-1.5 rounded-full bg-blue-50 px-2 py-0.5 text-xs font-medium text-blue-700">
          <span class="h-1.5 w-1.5 animate-pulse rounded-full bg-blue-500"></span>
          Running
        </span>
      {:else if scan.error}
        <span class="rounded-full bg-red-50 px-2 py-0.5 text-xs font-medium text-red-700">Failed</span>
      {:else if scan.finished_at}
        <span class="rounded-full bg-green-50 px-2 py-0.5 text-xs font-medium text-green-700">Idle</span>
      {:else}
        <span class="rounded-full bg-zinc-100 px-2 py-0.5 text-xs font-medium text-zinc-600">Never run</span>
      {/if}
    </div>

    {#if scan.running && scan.current_root_path}
      <p class="mt-2 text-xs text-zinc-500">Scanning: {scan.current_root_path}</p>
    {/if}
    {#if scan.error}
      <p class="mt-2 text-xs text-red-700">Error: {scan.error}</p>
    {/if}

    {#if scan.results.length > 0}
      <div class="mt-3 space-y-2">
        {#each scan.results as r}
          <div class="rounded border border-zinc-100 bg-zinc-50 p-2 text-xs">
            <div class="font-mono text-zinc-700">
              [{r.kind}] {r.path}
            </div>
            <div class="mt-1 text-zinc-600">
              {r.files_seen} files seen · {r.assets_added} added · {r.assets_updated} updated · {r.works_created} new works · {r.review_items_created} to review
              {#if r.errors.length > 0}
                · <span class="text-red-700">{r.errors.length} errors</span>
              {/if}
            </div>
          </div>
        {/each}
      </div>
    {/if}
  </div>
{/if}

<div class="mt-8 rounded-lg border border-zinc-200 bg-white p-6 text-sm text-zinc-600">
  <p class="font-medium text-zinc-900">Read-only by design</p>
  <p class="mt-2">
    BookLedger never writes to your library or download folders. Mount them with
    <code class="rounded bg-zinc-100 px-1.5 py-0.5 font-mono text-xs">:ro</code>
    in your compose file and the kernel will enforce it. The scanner only opens files
    in read mode to extract metadata.
  </p>
</div>
