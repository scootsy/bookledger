<script lang="ts">
  import { onMount } from 'svelte';
  import {
    api,
    COVERAGE_OPTIONS,
    type Tag,
    type WorkListResponse
  } from '$lib/api';

  let data = $state<WorkListResponse | null>(null);
  let tags = $state<Tag[]>([]);
  let error = $state<string | null>(null);
  let loading = $state(false);

  let q = $state('');
  let coverage = $state<string>('all');
  let selectedTags = $state<string[]>([]);
  let excludedTags = $state<string[]>(['ignored']);
  let offset = $state(0);
  const limit = 100;

  async function load() {
    loading = true;
    try {
      const params = new URLSearchParams();
      if (q.trim()) params.set('q', q.trim());
      if (coverage !== 'all') params.set('coverage', coverage);
      for (const t of selectedTags) params.append('tag', t);
      for (const t of excludedTags) params.append('exclude_tag', t);
      params.set('limit', String(limit));
      params.set('offset', String(offset));
      data = await api<WorkListResponse>(`/works?${params.toString()}`);
      error = null;
    } catch (e) {
      error = e instanceof Error ? e.message : String(e);
    } finally {
      loading = false;
    }
  }

  function toggleTagFilter(slug: string, list: string[]): string[] {
    return list.includes(slug) ? list.filter((s) => s !== slug) : [...list, slug];
  }

  onMount(async () => {
    try {
      tags = await api<Tag[]>('/tags');
    } catch {
      tags = [];
    }
    await load();
  });

  let searchDebounce: ReturnType<typeof setTimeout> | null = null;
  function onSearchInput() {
    if (searchDebounce) clearTimeout(searchDebounce);
    searchDebounce = setTimeout(() => {
      offset = 0;
      load();
    }, 250);
  }

  function onFilterChange() {
    offset = 0;
    load();
  }
</script>

<div class="mb-4 flex items-center justify-between">
  <h1 class="text-2xl font-semibold tracking-tight">Library</h1>
  {#if data}
    <span class="text-sm text-zinc-500">{data.total} works</span>
  {/if}
</div>

<div class="mb-4 space-y-3 rounded-lg border border-zinc-200 bg-white p-3">
  <div class="flex flex-wrap items-end gap-3">
    <input
      type="search"
      bind:value={q}
      oninput={onSearchInput}
      placeholder="Search title or author"
      class="grow rounded border border-zinc-300 bg-white px-3 py-1.5 text-sm"
    />
    <select
      bind:value={coverage}
      onchange={onFilterChange}
      class="rounded border border-zinc-300 bg-white px-2 py-1.5 text-sm"
    >
      {#each COVERAGE_OPTIONS as opt}
        <option value={opt.value}>{opt.label}</option>
      {/each}
    </select>
  </div>

  {#if tags.length > 0}
    <div class="flex flex-wrap items-center gap-1.5 text-xs">
      <span class="text-zinc-500">Include:</span>
      {#each tags as t}
        <button
          onclick={() => {
            selectedTags = toggleTagFilter(t.slug, selectedTags);
            onFilterChange();
          }}
          class="rounded-full border px-2 py-0.5"
          class:bg-zinc-900={selectedTags.includes(t.slug)}
          class:text-white={selectedTags.includes(t.slug)}
          class:border-zinc-900={selectedTags.includes(t.slug)}
          class:border-zinc-300={!selectedTags.includes(t.slug)}
        >
          {t.label}
        </button>
      {/each}
    </div>
    <div class="flex flex-wrap items-center gap-1.5 text-xs">
      <span class="text-zinc-500">Exclude:</span>
      {#each tags as t}
        <button
          onclick={() => {
            excludedTags = toggleTagFilter(t.slug, excludedTags);
            onFilterChange();
          }}
          class="rounded-full border px-2 py-0.5"
          class:bg-red-50={excludedTags.includes(t.slug)}
          class:text-red-700={excludedTags.includes(t.slug)}
          class:border-red-300={excludedTags.includes(t.slug)}
          class:border-zinc-300={!excludedTags.includes(t.slug)}
        >
          {t.label}
        </button>
      {/each}
    </div>
  {/if}
</div>

{#if error}
  <div class="rounded border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div>
{:else if !data}
  <p class="text-sm text-zinc-500">Loading…</p>
{:else if data.items.length === 0}
  <div class="rounded-lg border border-dashed border-zinc-300 bg-white p-12 text-center text-sm text-zinc-600">
    {#if data.total === 0 && !q && coverage === 'all'}
      No works yet. Go to <a href="/sources" class="underline">Sources</a> to add a library root, then scan.
    {:else}
      No works match these filters.
    {/if}
  </div>
{:else}
  <div class="overflow-hidden rounded-lg border border-zinc-200 bg-white">
    <table class="w-full text-sm">
      <thead class="bg-zinc-50 text-left text-xs uppercase tracking-wide text-zinc-500">
        <tr>
          <th class="px-3 py-2">Title</th>
          <th class="px-3 py-2">Author</th>
          <th class="px-3 py-2">Series</th>
          <th class="px-3 py-2 text-center">Ebook</th>
          <th class="px-3 py-2 text-center">Audio</th>
          <th class="px-3 py-2">Tags</th>
        </tr>
      </thead>
      <tbody>
        {#each data.items as w}
          <tr class="border-t border-zinc-100 hover:bg-zinc-50">
            <td class="px-3 py-2">
              <a href={`/works/${w.id}`} class="font-medium hover:underline">{w.title}</a>
              {#if w.publication_year}
                <span class="ml-1 text-xs text-zinc-500">({w.publication_year})</span>
              {/if}
            </td>
            <td class="px-3 py-2 text-zinc-700">
              {w.authors.length > 0 ? w.authors.join(', ') : w.sort_author}
            </td>
            <td class="px-3 py-2 text-xs text-zinc-600">
              {#if w.series}
                {w.series}{w.series_position ? ` #${w.series_position}` : ''}
              {:else}
                —
              {/if}
            </td>
            <td class="px-3 py-2 text-center">
              {#if w.ebook_count > 0}
                <span class="inline-block rounded bg-green-100 px-1.5 py-0.5 text-xs font-medium text-green-800">
                  {w.ebook_count}
                </span>
              {:else}
                <span class="text-zinc-300">—</span>
              {/if}
            </td>
            <td class="px-3 py-2 text-center">
              {#if w.audiobook_count > 0}
                <span class="inline-block rounded bg-purple-100 px-1.5 py-0.5 text-xs font-medium text-purple-800">
                  {w.audiobook_count}
                </span>
              {:else}
                <span class="text-zinc-300">—</span>
              {/if}
            </td>
            <td class="px-3 py-2">
              <div class="flex flex-wrap gap-1">
                {#each w.tags as t}
                  <span class="rounded-full bg-zinc-100 px-1.5 py-0.5 text-xs text-zinc-700">{t.label}</span>
                {/each}
              </div>
            </td>
          </tr>
        {/each}
      </tbody>
    </table>
  </div>

  {#if data.total > limit}
    <div class="mt-3 flex items-center justify-between text-sm">
      <button
        onclick={() => {
          offset = Math.max(0, offset - limit);
          load();
        }}
        disabled={offset === 0 || loading}
        class="rounded border border-zinc-300 px-3 py-1 hover:bg-zinc-50 disabled:opacity-50"
      >
        Previous
      </button>
      <span class="text-zinc-500">
        {offset + 1}–{Math.min(offset + limit, data.total)} of {data.total}
      </span>
      <button
        onclick={() => {
          offset = offset + limit;
          load();
        }}
        disabled={offset + limit >= data.total || loading}
        class="rounded border border-zinc-300 px-3 py-1 hover:bg-zinc-50 disabled:opacity-50"
      >
        Next
      </button>
    </div>
  {/if}
{/if}
