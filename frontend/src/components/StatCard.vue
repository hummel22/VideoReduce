<template>
  <article class="stat-card">
    <header class="stat-header">
      <span class="label">{{ label }}</span>
      <slot name="icon">
        <span class="default-icon" aria-hidden="true">⬤</span>
      </slot>
    </header>
    <p class="value">{{ value }}</p>
    <p class="description">{{ description }}</p>
  </article>
</template>

<script setup>
defineProps({
  label: {
    type: String,
    required: true
  },
  value: {
    type: [String, Number],
    required: true
  },
  description: {
    type: String,
    default: ''
  }
});
</script>

<style scoped>
.stat-card {
  background: white;
  border-radius: 1.25rem;
  padding: 1.5rem;
  display: grid;
  gap: 0.85rem;
  box-shadow: 0 18px 40px rgba(15, 23, 42, 0.08);
  border: 1px solid rgba(226, 232, 240, 0.6);
  min-height: 170px;
}

.stat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  text-transform: uppercase;
  font-size: 0.75rem;
  letter-spacing: 0.08em;
  color: #64748b;
}

.value {
  margin: 0;
  font-size: 2.45rem;
  font-weight: 600;
  color: #0f172a;
}

.description {
  margin: 0;
  font-size: 0.95rem;
  color: #475569;
}

.default-icon {
  font-size: 0.6rem;
  color: rgba(14, 165, 233, 0.65);
}
</style>
