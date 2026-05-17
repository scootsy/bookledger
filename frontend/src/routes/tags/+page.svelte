<script lang="ts">
  import { onMount } from 'svelte';
  import { api, type Tag } from '$lib/api';

  let tags = $state<Tag[]>([]);
  let error = $state<string | null>(null);
  let loaded = $state(false);

  let newSlug = $state('');
  let newLabel = $state('');
  let newColor = $state('#94a3b8');

  async function load() {
    try {
      tags = await api<Tag[]>('/tags');
      error = null;
    } catch (e) {
      error = e instanceof Error ? e.message : String(e);
    } finally {
      loaded = true;
    }
  }

  async function create() {
    if (!newSlug.trim() || !newLabel.trim()) return;
    try {
      await api('/tags', {
        method: 'POST',
        body: JSON.stringify({
          slug: newSlug.trim().toLowerCase(),
          label: newLabel.trim(),
          color: newColor
        })
      });
      newSlug = '';
      newLabel = '';
      await load();
    } catch (e) {
      error = e instanceof Error ? e.message : String(e);
    }
  }

  async function remove(tag: Tag) {
    if (!confirm(`Delete tag "${tag.label}"? This removes it from all works.`)) return;
    try {
      await api(`/tags/${tag.id}`, { method: 'DELETE' });
      await load();
    } catch (e) {
      error = e instanceof Error ? e.message : String(e);
    }
  }

  onMount(load);
</script>

<h1 class="mb-6 text-2xl font-semibold tracking-tight">Tags</h1>

{#if error}
  <div class="mb-4 rounded border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div>
{/if}

<div class="mb-6 rounded-lg border border-zinc-200 bg-white p-4">
  <div class="text-sm font-medium">Add a tag</div>
  <div class="mt-3 flex flex-wrap items-end gap-3">
    <label class="flex flex-col gap-1 text-xs">
      <span class="font-medium text-zinc-600">Slug</span>
      <input
        type="text"
        bind:value={newSlug}
        placeholder="kebab-case"
        class="rounded border border-zinc-300 bg-white px-2 py-1.5 font-mono text-sm"
      />
    </label>
    <label class="flex grow flex-col gap-1 text-xs">
      <span class="font-medium text-zinc-600">Label</span>
      <input
        type="text"
        bind:value={newLabel}
        class="rounded border border-zinc-300 bg-white px-2 py-1.5 text-sm"
      />
    </label>
    <label class="flex flex-col gap-1 text-xs">
      <span class="font-medium text-zinc-600">Color</span>
      <input
        type="color"
        bind:value={newColor}
        class="h-8 w-12 rounded border border-zinc-300"
      />
    </label>
    <button
      onclick={create}
      class="rounded bg-zinc-900 px-4 py-1.5 text-sm font-medium text-white hover:bg-zinc-800 disabled:opacity-50"
      disabled={!newSlug.trim() || !newLabel.trim()}
    >
      Add
    </button>
  </div>
</div>

{#if !loaded}
  <p class="text-sm text-zinc-500">Loading…</p>
{:else if tags.length === 0}
  <div class="rounded-lg border border-dashed border-zinc-300 bg-white p-12 text-center text-sm text-zinc-600">
    No tags yet.
  </div>
{:else}
  <ul class="space-y-2">
    {#each tags as t}
      <li class="flex items-center justify-between rounded border border-zinc-200 bg-white p-3">
        <span class="flex items-center gap-3">
          {#if t.color}
            <span class="h-3 w-3 rounded-full" style="background-color: {t.color}"></span>
          {/if}
          <span class="text-sm font-medium">{t.label}</span>
          <span class="font-mono text-xs text-zinc-500">{t.slug}</span>
        </span>
        <button
          onclick={() => remove(t)}
          class="rounded border border-red-300 px-2 py-1 text-xs text-red-700 hover:bg-red-50"
        >
          Delete
        </button>
      </li>
    {/each}
  </ul>
{/if}
