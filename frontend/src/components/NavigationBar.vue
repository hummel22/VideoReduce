<template>
  <aside class="nav-shell">
    <header class="nav-header">
      <div class="brand-circle">VR</div>
      <div class="brand-copy">
        <p class="brand-title">VideoReduce</p>
        <p class="brand-subtitle">Operations Console</p>
      </div>
    </header>
    <nav class="nav-links">
      <button
        v-for="item in items"
        :key="item.id"
        type="button"
        class="nav-link"
        :class="{ active: item.id === active }"
        @click="$emit('navigate', item.id)"
      >
        <span class="icon" aria-hidden="true">{{ item.icon }}</span>
        <span>{{ item.label }}</span>
      </button>
    </nav>
    <footer class="nav-footer">
      <p class="footer-title">Transfer health</p>
      <slot name="footer">
        <p class="footer-copy">Monitor SMB throughput and queue velocity from the dashboard.</p>
      </slot>
    </footer>
  </aside>
</template>

<script setup>
const props = defineProps({
  active: {
    type: String,
    required: true
  }
});

const items = [
  { id: 'dashboard', label: 'Dashboard', icon: '📊' },
  { id: 'queue', label: 'Queue monitor', icon: '🎞️' },
  { id: 'configuration', label: 'Configuration', icon: '⚙️' },
  { id: 'users', label: 'Administrators', icon: '🛡️' }
];
</script>

<style scoped>
.nav-shell {
  display: flex;
  flex-direction: column;
  padding: 2rem 1.5rem;
  background: #111826;
  color: #f1f5f9;
  gap: 2rem;
}

.nav-header {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.brand-circle {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: linear-gradient(135deg, #2563eb, #0ea5e9);
  font-weight: 700;
}

.brand-copy {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.brand-title {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 600;
}

.brand-subtitle {
  margin: 0;
  font-size: 0.85rem;
  color: rgba(241, 245, 249, 0.72);
}

.nav-links {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.9rem 1.1rem;
  border-radius: 0.85rem;
  border: none;
  background: transparent;
  color: inherit;
  cursor: pointer;
  transition: background 0.2s ease, transform 0.2s ease;
  text-align: left;
}

.nav-link:hover {
  background: rgba(148, 163, 184, 0.16);
  transform: translateX(3px);
}

.nav-link.active {
  background: rgba(96, 165, 250, 0.25);
  color: #e0f2fe;
}

.icon {
  font-size: 1.25rem;
}

.nav-footer {
  margin-top: auto;
  background: rgba(15, 23, 42, 0.64);
  border-radius: 1.25rem;
  padding: 1.25rem;
  font-size: 0.9rem;
  line-height: 1.4;
}

.footer-title {
  margin: 0 0 0.5rem;
  text-transform: uppercase;
  font-size: 0.75rem;
  letter-spacing: 0.08em;
  color: rgba(148, 163, 184, 0.86);
}

.footer-copy {
  margin: 0;
  color: rgba(226, 232, 240, 0.85);
}

@media (max-width: 960px) {
  .nav-shell {
    flex-direction: row;
    align-items: center;
    padding: 1rem;
  }

  .nav-links {
    flex-direction: row;
    flex-wrap: wrap;
    gap: 0.75rem;
  }

  .nav-footer {
    display: none;
  }
}
</style>
