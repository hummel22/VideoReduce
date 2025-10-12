<template>
  <section class="queue-view">
    <header class="header">
      <div>
        <h1>Queue monitor</h1>
        <p>Review ingest activity and monitor transcoding progression in real-time.</p>
      </div>
      <button type="button" class="refresh" @click="loadJobs">
        Refresh data
      </button>
    </header>
    <JobTable
      title="In-flight jobs"
      subtitle="Data reflects the most recent sync. Requires administrator credentials for live API access."
      :jobs="jobs"
    />
    <p v-if="error" class="error">
      {{ error }}
    </p>
  </section>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue';
import JobTable from '../components/JobTable.vue';
import { getQueueJobs } from '../api/client.js';

const jobs = reactive([]);
const error = ref('');

function toDisplayJob(job, index) {
  return {
    id: job.id ?? index,
    videoName: job.video_name ?? job.videoName ?? job.title ?? 'Untitled job',
    stage: job.stage ?? job.currentStage ?? 'queued',
    status: job.status ?? job.state ?? 'pending',
    progress: Math.round(job.progress ?? job.percentComplete ?? 0),
    profile: job.requested_profile ?? job.profile ?? 'default',
    duration: job.duration ?? '—',
    size: job.file_size_mb ? `${job.file_size_mb} MB` : job.size ?? '—'
  };
}

function seedJobs() {
  return [
    {
      id: 101,
      videoName: 'marketing-reel.mov',
      stage: 'transcoding',
      status: 'running',
      progress: 64,
      profile: 'default-hq',
      duration: '04:12',
      size: '842 MB'
    },
    {
      id: 102,
      videoName: 'q4-townhall.mp4',
      stage: 'uploading',
      status: 'pending',
      progress: 32,
      profile: 'mobile',
      duration: '48:20',
      size: '3.1 GB'
    },
    {
      id: 103,
      videoName: 'engineering-demo.mkv',
      stage: 'verifying',
      status: 'awaiting-review',
      progress: 92,
      profile: 'extra-high-quality',
      duration: '11:02',
      size: '1.8 GB'
    }
  ];
}

async function loadJobs() {
  error.value = '';
  jobs.splice(0, jobs.length, ...seedJobs());
  try {
    const response = await getQueueJobs();
    if (Array.isArray(response)) {
      jobs.splice(0, jobs.length, ...response.map(toDisplayJob));
    }
  } catch (err) {
    error.value =
      'Unable to reach the authenticated queue endpoint. Showing the latest cached sample data instead.';
    console.warn('Queue API unreachable', err);
  }
}

onMounted(loadJobs);
</script>

<style scoped>
.queue-view {
  display: grid;
  gap: 2rem;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: white;
  padding: 1.75rem 2rem;
  border-radius: 1.5rem;
  box-shadow: 0 18px 45px rgba(15, 23, 42, 0.05);
}

.header h1 {
  margin: 0 0 0.35rem;
}

.header p {
  margin: 0;
  color: #475569;
}

.refresh {
  border: none;
  background: linear-gradient(135deg, #2563eb, #0ea5e9);
  color: white;
  padding: 0.65rem 1.5rem;
  border-radius: 999px;
  font-weight: 600;
  cursor: pointer;
  box-shadow: 0 12px 24px rgba(14, 165, 233, 0.35);
}

.refresh:hover {
  filter: brightness(1.05);
}

.error {
  margin: 0;
  color: #b45309;
  background: rgba(251, 191, 36, 0.18);
  border-radius: 1rem;
  padding: 0.9rem 1.2rem;
}

@media (max-width: 720px) {
  .header {
    flex-direction: column;
    align-items: stretch;
    gap: 1rem;
  }

  .refresh {
    width: 100%;
  }
}
</style>
