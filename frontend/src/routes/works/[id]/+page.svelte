<script lang="ts">
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import {
    api,
    AUDIENCE_OPTIONS,
    formatBytes,
    formatDuration,
    type Tag,
    type WorkDetail
  } from '$lib/api';

  let work = $state<WorkDetail | null>(null);
  let allTags = $state<Tag[]>([]);
  let error = $state<string | null>(null);
  let saving = $state(false);

  let audience = $state('');
  let notes = $state('');
  let selectedTagSlugs = $state<string[]>([]);

  async function load() {
    const id = $page.params.id;
    try {
      const [w, t] = await Promise.all([
        api<WorkDetail>(`/works/${id}`),
        api<Tag[]>('/tags')
      ]);
      work = w;
      allTags = t;
      audience = w.audience ?? '';
      notes = w.notes ?? '';
      selectedTagSlugs = w.tags.map((t) => t.slug);
      error = null;
    } catch (e) {
      error = e instanceof Error ? e.message : String(e);
    }
  }

  async function save() {
    if (!work) return;
    saving = true;
    try {
      await api(`/works/${work.id}`, {
        method: 'PATCH',
        body: JSON.stringify({
          audience: audience || null,
          notes: notes || null,
          tag_slugs: selectedTagSlugs
        })
      });
      await load();
    } catch (e) {
      error = e instanceof Error ? e.message : String(e);
    } finally {
      saving = false;
    }
  }

  function toggleTag(slug: string) {
    selectedTagSlugs = selectedTagSlugs.includes(slug)
      ? selectedTagSlugs.filter((s) => s !== slug)
      : [...selectedTagSlugs, slug];
  }

  onMount(load);
</script>

<a href="/library" class="mb-4 inline-block text-sm text-zinc-500 hover:underline">← Library</a>

{#if error}
  <div class="rounded border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div>
{:else if !work}
  <p class="text-sm text-zinc-500">Loading…</p>
{:else}
  <div class="mb-6">
    <h1 class="text-2xl font-semibold tracking-tight">{work.title}</h1>
    <p class="mt-1 text-sm text-zinc-600">
      {work.authors.join(', ') || work.sort_author}
      {#if work.publication_year}
        · {work.publication_year}
      {/if}
      {#if work.series}
        · {work.series}{work.series_position ? ` #${work.series_position}` : ''}
      {/if}
    </p>
  </div>

  <div class="grid gap-6 md:grid-cols-3">
    <div class="md:col-span-2 space-y-4">
      <section class="rounded-lg border border-zinc-200 bg-white">
        <header class="border-b border-zinc-100 px-4 py-2 text-sm font-medium">
          Assets ({work.assets.length})
        </header>
        {#if work.assets.length === 0}
          <p class="px-4 py-6 text-sm text-zinc-500">No assets linked to this work.</p>
        {:else}
          <ul class="divide-y divide-zinc-100">
            {#each work.assets as a}
              <li class="px-4 py-3 text-sm">
                <div class="flex items-center justify-between gap-3">
                  <span class="inline-flex items-center gap-2">
                    <span
                      class="rounded px-1.5 py-0.5 text-xs font-medium"
                      class:bg-green-100={a.type === 'ebook'}
                      class:text-green-800={a.type === 'ebook'}
                      class:bg-purple-100={a.type === 'audiobook'}
                      class:text-purple-800={a.type === 'audiobook'}
                    >
                      {a.type}
                    </span>
                    {#if a.format}
                      <span class="font-mono text-xs text-zinc-600">.{a.format}</span>
                    {/if}
                    <span class="text-xs text-zinc-500">via {a.source_kind}</span>
                  </span>
                  <span class="text-xs text-zinc-500">
                    {formatBytes(a.size_bytes)}
                    {#if a.duration_seconds}
                      · {formatDuration(a.duration_seconds)}
                    {/if}
                  </span>
                </div>
                {#if a.path}
                  <p class="mt-1 font-mono text-xs text-zinc-500">{a.path}</p>
                {/if}
                {#if a.narrator}
                  <p class="mt-1 text-xs text-zinc-600">Narrator: {a.narrator}</p>
                {/if}
              </li>
            {/each}
          </ul>
        {/if}
      </section>

      {#if Object.keys(work.identifiers).length > 0}
        <section class="rounded-lg border border-zinc-200 bg-white p-4">
          <h2 class="mb-2 text-sm font-medium">Identifiers</h2>
          <dl class="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
            {#each Object.entries(work.identifiers) as [scheme, value]}
              <dt class="font-mono uppercase text-zinc-500">{scheme}</dt>
              <dd class="font-mono">{value}</dd>
            {/each}
          </dl>
        </section>
      {/if}
    </div>

    <aside class="space-y-4">
      <section class="rounded-lg border border-zinc-200 bg-white p-4">
        <h2 class="mb-3 text-sm font-medium">Metadata</h2>
        <label class="flex flex-col gap-1 text-xs">
          <span class="font-medium text-zinc-600">Audience</span>
          <select bind:value={audience} class="rounded border border-zinc-300 bg-white px-2 py-1.5 text-sm">
            <option value="">—</option>
            {#each AUDIENCE_OPTIONS as opt}
              <option value={opt.value}>{opt.label}</option>
            {/each}
          </select>
        </label>
        <label class="mt-3 flex flex-col gap-1 text-xs">
          <span class="font-medium text-zinc-600">Notes</span>
          <textarea
            bind:value={notes}
            rows="3"
            class="rounded border border-zinc-300 bg-white px-2 py-1.5 text-sm"
          ></textarea>
        </label>
      </section>

      <section class="rounded-lg border border-zinc-200 bg-white p-4">
        <h2 class="mb-3 text-sm font-medium">Tags</h2>
        <div class="flex flex-wrap gap-1.5">
          {#each allTags as t}
            <button
              onclick={() => toggleTag(t.slug)}
              class="rounded-full border px-2 py-0.5 text-xs"
              class:bg-zinc-900={selectedTagSlugs.includes(t.slug)}
              class:text-white={selectedTagSlugs.includes(t.slug)}
              class:border-zinc-900={selectedTagSlugs.includes(t.slug)}
              class:border-zinc-300={!selectedTagSlugs.includes(t.slug)}
            >
              {t.label}
            </button>
          {/each}
        </div>
      </section>

      <button
        onclick={save}
        disabled={saving}
        class="w-full rounded bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-800 disabled:opacity-50"
      >
        {saving ? 'Saving…' : 'Save changes'}
      </button>
    </aside>
  </div>
{/if}
