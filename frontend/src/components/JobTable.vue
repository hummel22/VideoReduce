<template>
  <section class="table-card">
    <header class="table-header">
      <h2>{{ title }}</h2>
      <p>{{ subtitle }}</p>
    </header>
    <table>
      <thead>
        <tr>
          <th>Video</th>
          <th>Stage</th>
          <th>Status</th>
          <th>Progress</th>
          <th>Profile</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="job in jobs" :key="job.id">
          <td>
            <span class="video-name">{{ job.videoName }}</span>
            <span class="meta">{{ job.duration }} · {{ job.size }}</span>
          </td>
          <td>{{ job.stage }}</td>
          <td>{{ job.status }}</td>
          <td>
            <div class="progress">
              <div class="bar" :style="{ width: job.progress + '%' }"></div>
            </div>
          </td>
          <td>{{ job.profile }}</td>
        </tr>
        <tr v-if="jobs.length === 0">
          <td colspan="5" class="empty">No jobs to display.</td>
        </tr>
      </tbody>
    </table>
  </section>
</template>

<script setup>
defineProps({
  title: {
    type: String,
    default: 'Queue jobs'
  },
  subtitle: {
    type: String,
    default: ''
  },
  jobs: {
    type: Array,
    default: () => []
  }
});
</script>

<style scoped>
.table-card {
  background: white;
  border-radius: 1.5rem;
  box-shadow: 0 18px 45px rgba(15, 23, 42, 0.05);
  overflow: hidden;
}

.table-header {
  padding: 1.75rem 2rem 1.25rem;
  border-bottom: 1px solid rgba(226, 232, 240, 0.7);
}

.table-header h2 {
  margin: 0 0 0.35rem;
}

.table-header p {
  margin: 0;
  color: #64748b;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th {
  text-align: left;
  font-size: 0.85rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #94a3b8;
  padding: 0.85rem 2rem;
}

td {
  padding: 1.1rem 2rem;
  border-bottom: 1px solid rgba(226, 232, 240, 0.6);
  vertical-align: middle;
}

tr:last-child td {
  border-bottom: none;
}

.video-name {
  display: block;
  font-weight: 600;
}

.meta {
  color: #64748b;
  font-size: 0.85rem;
}

.progress {
  background: rgba(148, 163, 184, 0.2);
  border-radius: 999px;
  overflow: hidden;
  height: 0.5rem;
}

.bar {
  height: 100%;
  background: linear-gradient(90deg, #2563eb, #38bdf8);
}

.empty {
  text-align: center;
  color: #64748b;
  padding: 2.5rem 0;
}
</style>
