<script lang="ts">
  import { onMount } from 'svelte';
  import { api, type Work } from '$lib/api';

  let works = $state<Work[]>([]);
  let error = $state<string | null>(null);
  let loaded = $state(false);

  onMount(async () => {
    try {
      works = await api<Work[]>('/works');
    } catch (e) {
      error = e instanceof Error ? e.message : String(e);
    } finally {
      loaded = true;
    }
  });
</script>

<div class="mb-6 flex items-center justify-between">
  <h1 class="text-2xl font-semibold tracking-tight">Library</h1>
  <input
    type="search"
    placeholder="Search…"
    class="rounded border border-zinc-300 bg-white px-3 py-1.5 text-sm"
    disabled
  />
</div>

{#if error}
  <div class="rounded border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div>
{:else if !loaded}
  <p class="text-sm text-zinc-500">Loading…</p>
{:else if works.length === 0}
  <div class="rounded-lg border border-dashed border-zinc-300 bg-white p-12 text-center">
    <p class="text-sm text-zinc-600">No works yet.</p>
    <p class="mt-1 text-xs text-zinc-500">Configure sources, then run a scan.</p>
  </div>
{:else}
  <div class="overflow-hidden rounded-lg border border-zinc-200 bg-white">
    <table class="w-full text-sm">
      <thead class="bg-zinc-50 text-left text-xs uppercase tracking-wide text-zinc-500">
        <tr>
          <th class="px-3 py-2">Title</th>
          <th class="px-3 py-2">Author</th>
          <th class="px-3 py-2">Series</th>
          <th class="px-3 py-2">Year</th>
        </tr>
      </thead>
      <tbody>
        {#each works as work}
          <tr class="border-t border-zinc-100">
            <td class="px-3 py-2 font-medium">{work.title}</td>
            <td class="px-3 py-2 text-zinc-600">{work.sort_author}</td>
            <td class="px-3 py-2 text-zinc-600">
              {work.series ?? '—'}{work.series_position ? ` #${work.series_position}` : ''}
            </td>
            <td class="px-3 py-2 text-zinc-600">{work.publication_year ?? '—'}</td>
          </tr>
        {/each}
      </tbody>
    </table>
  </div>
{/if}
