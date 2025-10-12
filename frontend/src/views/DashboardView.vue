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
      <ol>
        <li v-for="event in recentEvents" :key="event.id">
          <div class="event-meta">
            <span class="event-title">{{ event.title }}</span>
            <span class="event-time">{{ event.time }}</span>
          </div>
          <p>{{ event.description }}</p>
        </li>
      </ol>
    </section>
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue';
import StatCard from '../components/StatCard.vue';
import { getHealth } from '../api/client.js';

const healthStatus = ref('unknown');
const statistics = reactive({
  activeJobs: 4,
  averageThroughput: '62 min/h',
  smbLatency: '118 ms',
  storageBudget: '2.4 TB'
});

const recentEvents = reactive([
  {
    id: 1,
    title: 'Portfolio HQ-Streaming promoted',
    time: '2 minutes ago',
    description: 'Raised default transcoding preset for videos longer than 30 minutes.'
  },
  {
    id: 2,
    title: 'New upload from Android client',
    time: '11 minutes ago',
    description: 'Clip "studio-intro.mov" queued with the extra high quality flag.'
  },
  {
    id: 3,
    title: 'Queue catch-up complete',
    time: '1 hour ago',
    description: 'Backlog processed successfully. All outputs verified and mirrored to SMB output.'
  }
]);

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

@media (max-width: 720px) {
  .hero {
    flex-direction: column;
    gap: 1.5rem;
    text-align: center;
  }
}
</style>
