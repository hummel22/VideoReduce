<template>
  <section class="config-view">
    <header class="header">
      <div>
        <h1>Configuration</h1>
        <p>Document the SMB endpoints and encoding presets used by the Android clients.</p>
      </div>
      <button type="button" class="save" @click="persist">
        Save draft
      </button>
    </header>

    <div class="grid">
      <form class="panel" @submit.prevent="persist">
        <h2>SMB share</h2>
        <label>
          Hostname
          <input v-model="form.smb.host" type="text" placeholder="//storage.local/VideoReduce" />
        </label>
        <div class="field-grid">
          <label>
            Username
            <input v-model="form.smb.username" type="text" placeholder="transcode" />
          </label>
          <label>
            Password
            <input v-model="form.smb.password" type="password" placeholder="••••••••" />
          </label>
        </div>
        <div class="field-grid">
          <label>
            Input path
            <input v-model="form.smb.input" type="text" placeholder="/input" />
          </label>
          <label>
            Output path
            <input v-model="form.smb.output" type="text" placeholder="/output" />
          </label>
        </div>
        <p class="helper">Update credentials whenever the SMB share rotates secrets.</p>
      </form>

      <section class="panel presets">
        <h2>Encoding presets</h2>
        <div v-for="preset in form.presets" :key="preset.name" class="preset-card">
          <header>
            <div>
              <h3>{{ preset.name }}</h3>
              <p>{{ preset.description }}</p>
            </div>
            <span class="badge">{{ preset.tool }}</span>
          </header>
          <dl>
            <div>
              <dt>Target</dt>
              <dd>{{ preset.target }}</dd>
            </div>
            <div>
              <dt>Bitrate</dt>
              <dd>{{ preset.bitrate }}</dd>
            </div>
            <div>
              <dt>CRF</dt>
              <dd>{{ preset.crf }}</dd>
            </div>
            <div>
              <dt>Notes</dt>
              <dd>{{ preset.notes }}</dd>
            </div>
          </dl>
        </div>
      </section>
    </div>

    <p v-if="status" class="status-message">{{ status }}</p>
  </section>
</template>

<script setup>
import { reactive, ref } from 'vue';
import { listEncodingRules } from '../api/client.js';

const status = ref('');

const form = reactive({
  smb: {
    host: '//storage.local/VideoReduce',
    username: 'transcode',
    password: 'changeme',
    input: '/input',
    output: '/output'
  },
  presets: [
    {
      name: 'Default mobile',
      description: 'Balanced for quick review on Android devices.',
      target: '720p @ 24fps',
      bitrate: '2.5 Mbps',
      crf: 'CRF 23',
      tool: 'HandBrakeCLI',
      notes: 'Enforces AAC stereo audio.'
    },
    {
      name: 'Extra high quality',
      description: 'Preserves visually lossless output for hero content.',
      target: '4K @ 60fps',
      bitrate: '18 Mbps',
      crf: 'CRF 20',
      tool: 'FFmpeg',
      notes: 'Allocates 5.1 audio and mezzanine container.'
    }
  ]
});

async function persist() {
  status.value = 'Draft saved locally. Sync via the authenticated API when credentials are available.';
  try {
    const rules = await listEncodingRules();
    if (Array.isArray(rules) && rules.length > 0) {
      form.presets.splice(
        0,
        form.presets.length,
        ...rules.map((rule) => ({
          name: rule.name ?? `Rule ${rule.id}`,
          description: rule.description ?? 'Imported from backend',
          target: `${rule.min_resolution_height ?? '—'}p`,
          bitrate: rule.target_bitrate ?? rule.target ?? 'auto',
          crf: rule.crf ?? 'auto',
          tool: rule.tool ?? 'HandBrakeCLI',
          notes: rule.notes ?? 'Loaded from backend rule set.'
        }))
      );
      status.value = 'Live encoding rules synced from the backend API.';
    }
  } catch (error) {
    console.warn('Unable to load encoding rules', error);
  }
}
</script>

<style scoped>
.config-view {
  display: grid;
  gap: 2rem;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
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

.save {
  border: none;
  background: #111826;
  color: white;
  padding: 0.65rem 1.5rem;
  border-radius: 999px;
  font-weight: 600;
  cursor: pointer;
}

.grid {
  display: grid;
  gap: 2rem;
  grid-template-columns: minmax(0, 420px) minmax(0, 1fr);
}

.panel {
  background: white;
  border-radius: 1.5rem;
  padding: 2rem;
  box-shadow: 0 18px 45px rgba(15, 23, 42, 0.05);
  display: grid;
  gap: 1rem;
}

.panel h2 {
  margin: 0;
}

label {
  display: grid;
  gap: 0.4rem;
  color: #475569;
  font-size: 0.95rem;
}

input {
  border-radius: 0.75rem;
  border: 1px solid rgba(148, 163, 184, 0.5);
  padding: 0.75rem 1rem;
  font-size: 1rem;
}

.field-grid {
  display: grid;
  gap: 1rem;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.helper {
  margin: 0;
  font-size: 0.85rem;
  color: #64748b;
}

.presets {
  align-content: start;
}

.preset-card {
  border: 1px solid rgba(226, 232, 240, 0.8);
  border-radius: 1.25rem;
  padding: 1.5rem;
  display: grid;
  gap: 1rem;
}

.preset-card header {
  display: flex;
  justify-content: space-between;
  gap: 1.25rem;
  align-items: baseline;
}

.preset-card h3 {
  margin: 0 0 0.35rem;
}

.preset-card p {
  margin: 0;
  color: #475569;
}

.badge {
  padding: 0.35rem 0.75rem;
  border-radius: 999px;
  background: rgba(37, 99, 235, 0.16);
  color: #1d4ed8;
  font-size: 0.85rem;
  font-weight: 600;
}

dl {
  display: grid;
  gap: 1rem;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  margin: 0;
}

dl div {
  display: grid;
  gap: 0.3rem;
}

dt {
  font-size: 0.75rem;
  text-transform: uppercase;
  color: #94a3b8;
}

dd {
  margin: 0;
  font-weight: 600;
}

.status-message {
  margin: 0;
  background: rgba(37, 99, 235, 0.12);
  color: #1d4ed8;
  border-radius: 1rem;
  padding: 0.85rem 1.2rem;
}

@media (max-width: 960px) {
  .grid {
    grid-template-columns: 1fr;
  }

  .field-grid {
    grid-template-columns: 1fr;
  }
}
</style>
