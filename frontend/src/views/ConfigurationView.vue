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
        <template v-if="form.presets.length">
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
                <dt>Resolution</dt>
                <dd>{{ preset.resolution }}</dd>
              </div>
              <div>
                <dt>Video codec</dt>
                <dd>{{ preset.videoCodec }}</dd>
              </div>
              <div>
                <dt>Audio codec</dt>
                <dd>{{ preset.audioCodec }}</dd>
              </div>
              <div>
                <dt>Quality target</dt>
                <dd>{{ preset.qualityTarget }}</dd>
              </div>
              <div>
                <dt>Notes</dt>
                <dd>{{ preset.notes }}</dd>
              </div>
            </dl>
          </div>
        </template>
        <p v-else class="empty-presets">No encoding presets available.</p>
      </section>
    </div>

    <p v-if="status" class="status-message">{{ status }}</p>
  </section>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue';
import { getSmbConfiguration, listEncodingRules } from '../api/client.js';

const status = ref('');

const defaultPresets = Object.freeze([
  {
    name: 'Default mobile',
    description: 'Balanced for quick review on Android devices.',
    resolution: '720p @ 24fps',
    videoCodec: 'H.264',
    audioCodec: 'AAC Stereo',
    qualityTarget: 'CRF 23',
    tool: 'HandBrakeCLI',
    notes: 'Enforces AAC stereo audio.'
  },
  {
    name: 'Extra high quality',
    description: 'Preserves visually lossless output for hero content.',
    resolution: '4K @ 60fps',
    videoCodec: 'H.265',
    audioCodec: 'Dolby 5.1',
    qualityTarget: 'CRF 20',
    tool: 'FFmpeg',
    notes: 'Allocates 5.1 audio and mezzanine container.'
  }
]);

function cloneDefaultPresets() {
  return defaultPresets.map((preset) => ({ ...preset }));
}

const form = reactive({
  smb: {
    host: '',
    username: '',
    password: '',
    input: '',
    output: ''
  },
  presets: cloneDefaultPresets()
});

function formatNumber(value, fractionDigits = 0) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) {
    return String(value ?? '');
  }
  return numeric.toFixed(fractionDigits);
}

function describeRange(min, max, formatter) {
  const hasMin = min !== null && min !== undefined;
  const hasMax = max !== null && max !== undefined;
  if (!hasMin && !hasMax) {
    return '';
  }
  const format = formatter ?? ((value) => String(value));
  const formattedMin = hasMin ? format(min) : '';
  const formattedMax = hasMax ? format(max) : '';
  if (hasMin && hasMax) {
    if (formattedMin && formattedMax) {
      return `${formattedMin} – ${formattedMax}`;
    }
    if (formattedMin) {
      return `≥ ${formattedMin}`;
    }
    if (formattedMax) {
      return `≤ ${formattedMax}`;
    }
    return '';
  }
  if (hasMin && formattedMin) {
    return `≥ ${formattedMin}`;
  }
  if (hasMax && formattedMax) {
    return `≤ ${formattedMax}`;
  }
  return '';
}

function describeRule(rule) {
  const size = describeRange(rule.min_size_mb, rule.max_size_mb, (value) => `${formatNumber(value, 0)} MB`);
  const duration = describeRange(
    rule.min_duration_seconds,
    rule.max_duration_seconds,
    (value) => `${formatNumber(value / 60, 0)} min`
  );
  const resolution = describeRange(
    rule.min_resolution_height,
    rule.max_resolution_height,
    (value) => `${formatNumber(value, 0)}p`
  );
  const segments = [size ? `Size ${size}` : '', duration ? `Duration ${duration}` : '', resolution ? `Resolution ${resolution}` : '']
    .filter(Boolean);
  return segments.length ? segments.join(' • ') : 'Applies to all queue jobs.';
}

function mapRuleToPreset(rule) {
  const profile = rule.profile ?? {};
  const resolution = describeRange(
    rule.min_resolution_height,
    rule.max_resolution_height,
    (value) => `${formatNumber(value, 0)}p`
  );
  return {
    name: profile.name ?? rule.name ?? `Rule ${rule.id}`,
    description: describeRule(rule),
    resolution: resolution || 'Any resolution',
    videoCodec: profile.video_codec ? profile.video_codec.toUpperCase() : 'Auto',
    audioCodec: profile.audio_codec ? profile.audio_codec.toUpperCase() : 'Auto',
    qualityTarget: profile.quality_target ? profile.quality_target.toUpperCase() : 'Auto',
    tool: profile.tool ?? 'HandBrakeCLI',
    notes: rule.high_quality_only ? 'High quality jobs only' : 'Applies to all jobs.'
  };
}

function applyEncodingRules(rules) {
  if (Array.isArray(rules) && rules.length > 0) {
    form.presets.splice(0, form.presets.length, ...rules.map(mapRuleToPreset));
    return true;
  }
  form.presets.splice(0, form.presets.length, ...cloneDefaultPresets());
  return false;
}

async function persist() {
  status.value = 'Draft saved locally. Sync via the authenticated API when credentials are available.';
  try {
    const rules = await listEncodingRules();
    if (applyEncodingRules(rules)) {
      status.value = 'Live encoding rules synced from the backend API.';
    } else {
      status.value = 'No encoding rules returned by the backend API. Showing default presets.';
    }
  } catch (error) {
    console.warn('Unable to load encoding rules', error);
  }
}

async function loadSmbConfiguration() {
  try {
    const config = await getSmbConfiguration();
    form.smb.host = config.share_url ?? '';
    form.smb.username = config.username ?? '';
    form.smb.password = config.password ?? '';
    form.smb.input = config.input_path ?? '';
    form.smb.output = config.output_path ?? '';
  } catch (error) {
    console.warn('Unable to load SMB configuration', error);
  }
}

async function loadEncodingRules() {
  try {
    const rules = await listEncodingRules();
    if (!applyEncodingRules(rules)) {
      status.value = 'No encoding rules configured yet.';
    }
  } catch (error) {
    console.warn('Unable to load encoding rules', error);
    form.presets.splice(0, form.presets.length, ...cloneDefaultPresets());
    status.value = 'Unable to load encoding rules. Showing default presets. Check backend connectivity.';
  }
}

onMounted(() => {
  void loadSmbConfiguration();
  void loadEncodingRules();
});
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

.empty-presets {
  margin: 0;
  color: #94a3b8;
  font-style: italic;
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
