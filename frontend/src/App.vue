<template>
  <div class="app-shell">
    <NavigationBar
      :active="currentView"
      @navigate="handleNavigate"
    />
    <main class="app-content">
      <component :is="activeComponent" />
    </main>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue';
import NavigationBar from './components/NavigationBar.vue';
import DashboardView from './views/DashboardView.vue';
import QueueView from './views/QueueView.vue';
import ConfigurationView from './views/ConfigurationView.vue';
import UsersView from './views/UsersView.vue';

const views = {
  dashboard: DashboardView,
  queue: QueueView,
  configuration: ConfigurationView,
  users: UsersView
};

const currentView = ref('dashboard');

const activeComponent = computed(() => views[currentView.value] ?? DashboardView);

function handleNavigate(view) {
  currentView.value = view;
}
</script>

<style scoped>
.app-shell {
  display: grid;
  grid-template-columns: 280px 1fr;
  min-height: 100vh;
}

.app-content {
  padding: 2.5rem;
  background: linear-gradient(135deg, #f8fafc, #eef1f7);
  overflow-y: auto;
}

@media (max-width: 960px) {
  .app-shell {
    grid-template-columns: 1fr;
  }

  .app-content {
    padding: 1.5rem;
  }
}
</style>
