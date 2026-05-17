<script lang="ts">
  import { onMount } from 'svelte';
  import { api, type ReviewItem } from '$lib/api';

  let items = $state<ReviewItem[]>([]);
  let error = $state<string | null>(null);
  let loaded = $state(false);

  onMount(async () => {
    try {
      items = await api<ReviewItem[]>('/review');
    } catch (e) {
      error = e instanceof Error ? e.message : String(e);
    } finally {
      loaded = true;
    }
  });
</script>

<h1 class="mb-6 text-2xl font-semibold tracking-tight">Review queue</h1>

{#if error}
  <div class="rounded border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div>
{:else if !loaded}
  <p class="text-sm text-zinc-500">Loading…</p>
{:else if items.length === 0}
  <div class="rounded-lg border border-dashed border-zinc-300 bg-white p-12 text-center text-sm text-zinc-600">
    Nothing to review.
  </div>
{:else}
  <ul class="space-y-2">
    {#each items as item}
      <li class="rounded border border-zinc-200 bg-white p-3 text-sm">
        Asset #{item.asset_id} → Work #{item.candidate_work_id ?? '?'} (confidence {item.confidence.toFixed(2)})
      </li>
    {/each}
  </ul>
{/if}
