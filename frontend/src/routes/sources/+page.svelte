<script lang="ts">
  import { onDestroy, onMount } from 'svelte';
  import { api, type LibraryRoot, type ScanStatus } from '$lib/api';

  let roots = $state<LibraryRoot[]>([]);
  let scan = $state<ScanStatus | null>(null);
  let loaded = $state(false);
  let error = $state<string | null>(null);
  let polling: ReturnType<typeof setInterval> | null = null;

  let newKind = $state<'ebook' | 'audiobook'>('ebook');
  let newPath = $state('');
  let creating = $state(false);

  async function refresh() {
    try {
      const [r, s] = await Promise.all([
        api<LibraryRoot[]>('/sources'),
        api<ScanStatus>('/scan/status')
      ]);
      roots = r;
      scan = s;
      error = null;
    } catch (e) {
      error = e instanceof Error ? e.message : String(e);
    } finally {
      loaded = true;
    }
  }

  async function create() {
    if (!newPath.trim()) return;
    creating = true;
    try {
      await api('/sources', {
        method: 'POST',
        body: JSON.stringify({ kind: newKind, path: newPath.trim() })
      });
      newPath = '';
      await refresh();
    } catch (e) {
      error = e instanceof Error ? e.message : String(e);
    } finally {
      creating = false;
    }
  }

  async function toggle(root: LibraryRoot) {
    try {
      await api(`/sources/${root.id}`, {
        method: 'PATCH',
        body: JSON.stringify({ enabled: !root.enabled })
      });
      await refresh();
    } catch (e) {
      error = e instanceof Error ? e.message : String(e);
    }
  }

  async function remove(root: LibraryRoot) {
    if (!confirm(`Remove source ${root.path}? This only deletes the configuration — your files are untouched.`)) {
      return;
    }
    try {
      await api(`/sources/${root.id}`, { method: 'DELETE' });
      await refresh();
    } catch (e) {
      error = e instanceof Error ? e.message : String(e);
    }
  }

  async function scanOne(root: LibraryRoot) {
    try {
      await api(`/scan/run/${root.id}`, { method: 'POST' });
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

  function formatDate(iso: string | null): string {
    if (!iso) return 'never';
    const d = new Date(iso);
    return d.toLocaleString();
  }
</script>

<h1 class="mb-2 text-2xl font-semibold tracking-tight">Sources</h1>
<p class="mb-6 text-sm text-zinc-500">
  Library roots are paths inside the BookLedger container that hold ebook or audiobook
  files. Mount them <code class="rounded bg-zinc-100 px-1 font-mono text-xs">:ro</code>
  in your compose file — BookLedger only reads them.
</p>

{#if error}
  <div class="mb-4 rounded border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div>
{/if}

<div class="mb-6 rounded-lg border border-zinc-200 bg-white p-4">
  <div class="text-sm font-medium">Add a source</div>
  <div class="mt-3 flex flex-wrap items-end gap-3">
    <label class="flex flex-col gap-1 text-xs">
      <span class="font-medium text-zinc-600">Kind</span>
      <select
        bind:value={newKind}
        class="rounded border border-zinc-300 bg-white px-2 py-1.5 text-sm"
      >
        <option value="ebook">Ebook</option>
        <option value="audiobook">Audiobook</option>
      </select>
    </label>
    <label class="flex grow flex-col gap-1 text-xs">
      <span class="font-medium text-zinc-600">Container path</span>
      <input
        type="text"
        bind:value={newPath}
        placeholder="/libraries/books"
        class="rounded border border-zinc-300 bg-white px-2 py-1.5 font-mono text-sm"
      />
    </label>
    <button
      onclick={create}
      disabled={creating || !newPath.trim()}
      class="rounded bg-zinc-900 px-4 py-1.5 text-sm font-medium text-white hover:bg-zinc-800 disabled:opacity-50"
    >
      Add
    </button>
  </div>
</div>

{#if !loaded}
  <p class="text-sm text-zinc-500">Loading…</p>
{:else if roots.length === 0}
  <div class="rounded-lg border border-dashed border-zinc-300 bg-white p-12 text-center text-sm text-zinc-600">
    No sources configured yet. Add one above.
  </div>
{:else}
  <div class="overflow-hidden rounded-lg border border-zinc-200 bg-white">
    <table class="w-full text-sm">
      <thead class="bg-zinc-50 text-left text-xs uppercase tracking-wide text-zinc-500">
        <tr>
          <th class="px-3 py-2">Kind</th>
          <th class="px-3 py-2">Path</th>
          <th class="px-3 py-2">Status</th>
          <th class="px-3 py-2">Last scan</th>
          <th class="px-3 py-2"></th>
        </tr>
      </thead>
      <tbody>
        {#each roots as root}
          <tr class="border-t border-zinc-100">
            <td class="px-3 py-2">
              <span class="rounded bg-zinc-100 px-1.5 py-0.5 text-xs font-mono">{root.kind}</span>
            </td>
            <td class="px-3 py-2 font-mono text-xs">{root.path}</td>
            <td class="px-3 py-2 text-xs">
              {#if !root.path_exists}
                <span class="text-red-700">Path missing</span>
              {:else if !root.path_is_directory}
                <span class="text-red-700">Not a directory</span>
              {:else if !root.enabled}
                <span class="text-zinc-500">Disabled</span>
              {:else}
                <span class="text-green-700">Enabled</span>
              {/if}
            </td>
            <td class="px-3 py-2 text-xs text-zinc-600">{formatDate(root.last_scanned_at)}</td>
            <td class="px-3 py-2 text-right">
              <div class="flex justify-end gap-2 text-xs">
                <button
                  onclick={() => scanOne(root)}
                  disabled={scan?.running || !root.enabled || !root.path_exists}
                  class="rounded border border-zinc-300 px-2 py-1 hover:bg-zinc-50 disabled:opacity-50"
                  title={scan?.running ? 'A scan is already running' : 'Scan this source'}
                >
                  Scan
                </button>
                <button
                  onclick={() => toggle(root)}
                  class="rounded border border-zinc-300 px-2 py-1 hover:bg-zinc-50"
                >
                  {root.enabled ? 'Disable' : 'Enable'}
                </button>
                <button
                  onclick={() => remove(root)}
                  class="rounded border border-red-300 px-2 py-1 text-red-700 hover:bg-red-50"
                >
                  Remove
                </button>
              </div>
            </td>
          </tr>
        {/each}
      </tbody>
    </table>
  </div>
{/if}

{#if scan?.running}
  <p class="mt-3 text-xs text-blue-700">
    Scan running: {scan.current_root_path ?? '—'}
  </p>
{/if}
