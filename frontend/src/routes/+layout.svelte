<script lang="ts">
  import '../app.css';
  import { page } from '$app/stores';

  let { children } = $props();

  const nav = [
    { href: '/', label: 'Dashboard' },
    { href: '/library', label: 'Library' },
    { href: '/review', label: 'Review' },
    { href: '/sources', label: 'Sources' },
    { href: '/tags', label: 'Tags' }
  ];

  function isActive(href: string, pathname: string): boolean {
    if (href === '/') return pathname === '/';
    return pathname === href || pathname.startsWith(href + '/');
  }
</script>

<div class="min-h-screen bg-zinc-50 text-zinc-900">
  <header class="border-b border-zinc-200 bg-white">
    <div class="mx-auto flex max-w-7xl items-center justify-between px-4 py-3">
      <a href="/" class="text-lg font-semibold tracking-tight">BookLedger</a>
      <nav class="flex gap-1 text-sm">
        {#each nav as item}
          <a
            href={item.href}
            class="rounded px-3 py-1.5 transition-colors"
            class:bg-zinc-900={isActive(item.href, $page.url.pathname)}
            class:text-white={isActive(item.href, $page.url.pathname)}
            class:hover:bg-zinc-100={!isActive(item.href, $page.url.pathname)}
          >
            {item.label}
          </a>
        {/each}
      </nav>
    </div>
  </header>
  <main class="mx-auto max-w-7xl px-4 py-6">
    {@render children()}
  </main>
</div>
