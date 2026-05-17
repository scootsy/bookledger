<script lang="ts">
  import { onMount } from 'svelte';
  import { api, type Tag } from '$lib/api';

  let tags = $state<Tag[]>([]);
  let error = $state<string | null>(null);
  let loaded = $state(false);

  onMount(async () => {
    try {
      tags = await api<Tag[]>('/tags');
    } catch (e) {
      error = e instanceof Error ? e.message : String(e);
    } finally {
      loaded = true;
    }
  });
</script>

<h1 class="mb-6 text-2xl font-semibold tracking-tight">Tags</h1>

{#if error}
  <div class="rounded border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div>
{:else if !loaded}
  <p class="text-sm text-zinc-500">Loading…</p>
{:else if tags.length === 0}
  <div class="rounded-lg border border-dashed border-zinc-300 bg-white p-12 text-center text-sm text-zinc-600">
    No tags yet.
  </div>
{:else}
  <ul class="flex flex-wrap gap-2">
    {#each tags as tag}
      <li class="rounded-full border border-zinc-200 bg-white px-3 py-1 text-xs">
        {tag.label}
      </li>
    {/each}
  </ul>
{/if}
