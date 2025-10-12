<template>
  <section class="dashboard">
    <header class="hero">
      <div>
        <h1>Operations overview</h1>
        <p>Track the health of queue processing, SMB throughput, and transcoding velocity.</p>
      </div>
      <div class="status-pill" :class="statusClass">
        <span class="dot"></span>
        <span>{{ healthMessage }}</span>
      </div>
    </header>

    <div class="stat-grid">
      <StatCard
        label="Active jobs"
        :value="statistics.activeJobs"
        description="Currently processing across the worker pool"
      >
        <template #icon>
          <span class="hero-icon" aria-hidden="true">⚡</span>
        </template>
      </StatCard>
      <StatCard
        label="Average throughput"
        :value="statistics.averageThroughput"
        description="Transcode minutes per hour"
      >
        <template #icon>
          <span class="hero-icon" aria-hidden="true">🎚️</span>
        </template>
      </StatCard>
      <StatCard
        label="SMB latency"
        :value="statistics.smbLatency"
        description="Median read/write latency across the input share"
      >
        <template #icon>
          <span class="hero-icon" aria-hidden="true">📦</span>
        </template>
      </StatCard>
      <StatCard
        label="Storage budget"
        :value="statistics.storageBudget"
        description="Remaining allocated space across the output share"
      >
        <template #icon>
          <span class="hero-icon" aria-hidden="true">💾</span>
        </template>
      </StatCard>
    </div>

    <section class="timeline">
      <h2>Recent activity</h2>
      <ol v-if="recentEvents.length">
        <li v-for="event in recentEvents" :key="event.id">
          <div class="event-meta">
            <span class="event-title">{{ event.title }}</span>
            <span class="event-time">{{ event.time }}</span>
          </div>
          <p>{{ event.description }}</p>
        </li>
      </ol>
      <p v-else class="empty-state">No timeline activity recorded yet.</p>
    </section>
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue';
import StatCard from '../components/StatCard.vue';
import { getDashboardOverview, getHealth, listDashboardEvents } from '../api/client.js';

const healthStatus = ref('unknown');
const statistics = reactive({
  activeJobs: 0,
  averageThroughput: '0 min/h',
  smbLatency: '0 ms',
  storageBudget: '0 B'
});

const recentEvents = ref([]);

function formatThroughput(value) {
  if (!value) return '0 min/h';
  return `${Number(value).toFixed(1)} min/h`;
}

function formatLatency(value) {
  if (!value) return '0 ms';
  return `${Math.round(Number(value))} ms`;
}

function formatStorage(bytes) {
  const size = Number(bytes ?? 0);
  if (size <= 0) {
    return '0 B';
  }
  const units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB'];
  const exponent = Math.min(Math.floor(Math.log(size) / Math.log(1024)), units.length - 1);
  const value = size / 1024 ** exponent;
  return `${value.toFixed(exponent === 0 ? 0 : 1)} ${units[exponent]}`;
}

function formatTimestamp(isoString) {
  const date = new Date(isoString);
  if (Number.isNaN(date.getTime())) {
    return '';
  }
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short'
  }).format(date);
}

async function loadAnalytics() {
  try {
    const overview = await getDashboardOverview();
    statistics.activeJobs = overview.active_jobs ?? 0;
    statistics.averageThroughput = formatThroughput(overview.average_throughput_minutes);
    statistics.smbLatency = formatLatency(overview.smb_latency_ms);
    statistics.storageBudget = formatStorage(overview.storage_budget_bytes);
  } catch (error) {
    console.warn('Unable to load dashboard overview', error);
  }

  try {
    const events = await listDashboardEvents();
    recentEvents.value = events.map((event) => ({
      id: event.id,
      title: event.title,
      description: event.description,
      time: formatTimestamp(event.created_at)
    }));
  } catch (error) {
    console.warn('Unable to load dashboard events', error);
    recentEvents.value = [];
  }
}

const statusClass = computed(() => {
  switch (healthStatus.value) {
    case 'ok':
      return 'status-ok';
    case 'degraded':
      return 'status-warn';
    case 'unknown':
    default:
      return 'status-idle';
  }
});

const healthMessage = computed(() => {
  if (healthStatus.value === 'ok') {
    return 'Workers healthy';
  }
  if (healthStatus.value === 'degraded') {
    return 'Investigate queue delays';
  }
  return 'Health unknown';
});

onMounted(async () => {
  try {
    const response = await getHealth();
    healthStatus.value = response.status ?? 'ok';
  } catch (error) {
    console.warn('Unable to reach health endpoint', error);
    healthStatus.value = 'unknown';
  }
  await loadAnalytics();
});
</script>

<style scoped>
.dashboard {
  display: grid;
  gap: 2.5rem;
}

.hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: white;
  padding: 2rem;
  border-radius: 1.5rem;
  box-shadow: 0 18px 45px rgba(15, 23, 42, 0.1);
}

.hero h1 {
  margin: 0 0 0.6rem;
  font-size: 2.1rem;
}

.hero p {
  margin: 0;
  color: #475569;
  max-width: 32rem;
  line-height: 1.5;
}

.status-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.75rem;
  border-radius: 999px;
  padding: 0.65rem 1.2rem;
  font-weight: 600;
  font-size: 0.95rem;
}

.status-ok {
  background: rgba(34, 197, 94, 0.15);
  color: #15803d;
}

.status-warn {
  background: rgba(250, 204, 21, 0.25);
  color: #92400e;
}

.status-idle {
  background: rgba(148, 163, 184, 0.22);
  color: #334155;
}

.dot {
  width: 0.7rem;
  height: 0.7rem;
  border-radius: 50%;
  background: currentColor;
}

.stat-grid {
  display: grid;
  gap: 1.5rem;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
}

.hero-icon {
  font-size: 1.4rem;
}

.timeline {
  background: white;
  border-radius: 1.5rem;
  padding: 2rem;
  box-shadow: 0 18px 45px rgba(15, 23, 42, 0.05);
  display: grid;
  gap: 1.25rem;
}

.timeline h2 {
  margin-top: 0;
}

.timeline ol {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  gap: 1.4rem;
}

.timeline li {
  border-left: 3px solid rgba(148, 163, 184, 0.25);
  padding-left: 1.5rem;
  position: relative;
}

.timeline li::before {
  content: '';
  position: absolute;
  left: -1rem;
  top: 0.3rem;
  width: 0.65rem;
  height: 0.65rem;
  border-radius: 50%;
  background: #2563eb;
  box-shadow: 0 0 0 6px rgba(37, 99, 235, 0.12);
}

.event-meta {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
}

.event-title {
  font-weight: 600;
}

.event-time {
  font-size: 0.85rem;
  color: #64748b;
}

.timeline p {
  margin: 0.35rem 0 0;
  color: #475569;
}

.empty-state {
  margin: 0;
  color: #94a3b8;
}

@media (max-width: 720px) {
  .hero {
    flex-direction: column;
    gap: 1.5rem;
    text-align: center;
  }
}
</style>
