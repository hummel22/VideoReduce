<template>
  <section class="config-view">
    <header class="header">
      <div>
        <h1>Configuration</h1>
        <p>Document the SMB endpoints and encoding presets used by the Android clients.</p>
      </div>
      <div class="actions">
        <button type="button" class="ghost" @click="refreshEncodingRules()" :disabled="isSyncingPresets">
          <span v-if="isSyncingPresets">Refreshing…</span>
          <span v-else>Refresh presets</span>
        </button>
        <button type="button" class="ghost" @click="testConnection" :disabled="isTesting">
          <span v-if="isTesting">Testing…</span>
          <span v-else>Test connection</span>
        </button>
        <button type="button" class="save" @click="saveConfiguration" :disabled="isSaving">
          <span v-if="isSaving">Saving…</span>
          <span v-else>Save configuration</span>
        </button>
      </div>
    </header>

    <div class="grid">
      <form class="panel" @submit.prevent="saveConfiguration">
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

      <section class="panel smb-presets">
        <header class="panel-heading">
          <div>
            <h2>SMB presets</h2>
            <p>Save frequent SMB targets to quickly populate the form.</p>
          </div>
          <div class="preset-toolbar">
            <button type="button" class="ghost" @click="refreshSmbPresets()" :disabled="isLoadingPresets">
              <span v-if="isLoadingPresets">Refreshing…</span>
              <span v-else>Refresh</span>
            </button>
            <button type="button" class="ghost" @click="openCreatePresetDialog">New preset</button>
          </div>
        </header>
        <p v-if="isLoadingPresets" class="empty-presets">Loading SMB presets…</p>
        <template v-else-if="smbPresets.length">
          <article v-for="preset in smbPresets" :key="preset.id" class="smb-preset-card">
            <header>
              <div>
                <h3>{{ preset.name }}</h3>
                <p v-if="preset.description">{{ preset.description }}</p>
              </div>
              <div class="preset-actions">
                <button type="button" class="ghost" @click="applyPreset(preset)">Apply</button>
                <button type="button" class="ghost" @click="openEditPresetDialog(preset)">Edit</button>
                <button
                  type="button"
                  class="icon-button"
                  @click="openExportDialog(preset)"
                  aria-label="Export preset"
                >
                  <svg viewBox="0 0 24 24" aria-hidden="true">
                    <path
                      d="M5 3h14a2 2 0 0 1 2 2v6h-2V5H5v14h6v2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2zm11 10 4 4-4 4v-3h-7v-2h7v-3z"
                      fill="currentColor"
                    />
                  </svg>
                </button>
                <button type="button" class="ghost danger" @click="confirmDeletePreset(preset)">Delete</button>
              </div>
            </header>
            <dl>
              <div>
                <dt>Share URL</dt>
                <dd>{{ preset.share_url }}</dd>
              </div>
              <div>
                <dt>Username</dt>
                <dd>{{ preset.username }}</dd>
              </div>
              <div>
                <dt>Password</dt>
                <dd>{{ maskPassword(preset.password) }}</dd>
              </div>
              <div>
                <dt>Input path</dt>
                <dd>{{ preset.input_path }}</dd>
              </div>
              <div>
                <dt>Output path</dt>
                <dd>{{ preset.output_path }}</dd>
              </div>
            </dl>
          </article>
        </template>
        <p v-else class="empty-presets">No SMB presets saved yet.</p>
      </section>

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

    <div v-if="presetDialog.visible" class="modal-backdrop" @click.self="closePresetDialog">
      <div class="modal">
        <header class="modal-header">
          <h2>{{ presetDialog.mode === 'create' ? 'Create SMB preset' : 'Edit SMB preset' }}</h2>
          <button type="button" class="icon-button" @click="closePresetDialog" aria-label="Close dialog">
            <span aria-hidden="true">×</span>
          </button>
        </header>
        <form class="modal-body" @submit.prevent="submitPresetDialog">
          <label>
            Preset name
            <input v-model="presetDialog.form.name" type="text" placeholder="Studio NAS" />
          </label>
          <label>
            Description
            <textarea
              v-model="presetDialog.form.description"
              rows="2"
              placeholder="Optional notes about this SMB share"
            ></textarea>
          </label>
          <label>
            Share URL
            <input v-model="presetDialog.form.shareUrl" type="text" placeholder="//storage.local/VideoReduce" />
          </label>
          <div class="field-grid">
            <label>
              Username
              <input v-model="presetDialog.form.username" type="text" placeholder="transcode" />
            </label>
            <label>
              Password
              <input v-model="presetDialog.form.password" type="text" placeholder="••••••••" />
            </label>
          </div>
          <div class="field-grid">
            <label>
              Input path
              <input v-model="presetDialog.form.inputPath" type="text" placeholder="/input" />
            </label>
            <label>
              Output path
              <input v-model="presetDialog.form.outputPath" type="text" placeholder="/output" />
            </label>
          </div>
          <p v-if="presetDialog.error" class="form-error">{{ presetDialog.error }}</p>
          <div class="modal-actions">
            <button type="button" class="ghost" @click="closePresetDialog" :disabled="presetDialog.isSaving">Cancel</button>
            <button type="submit" class="save" :disabled="presetDialog.isSaving">
              <span v-if="presetDialog.isSaving">{{ presetDialog.mode === 'create' ? 'Saving…' : 'Updating…' }}</span>
              <span v-else>{{ presetDialog.mode === 'create' ? 'Create preset' : 'Save changes' }}</span>
            </button>
          </div>
        </form>
      </div>
    </div>

    <div v-if="deleteDialog.visible" class="modal-backdrop" @click.self="closeDeleteDialog">
      <div class="modal">
        <header class="modal-header">
          <h2>Delete preset</h2>
          <button type="button" class="icon-button" @click="closeDeleteDialog" aria-label="Close dialog">
            <span aria-hidden="true">×</span>
          </button>
        </header>
        <p>
          Are you sure you want to delete the preset
          <strong>{{ deleteDialog.preset?.name }}</strong>?
        </p>
        <p v-if="deleteDialog.error" class="form-error">{{ deleteDialog.error }}</p>
        <div class="modal-actions">
          <button type="button" class="ghost" @click="closeDeleteDialog" :disabled="deleteDialog.isDeleting">Cancel</button>
          <button
            type="button"
            class="ghost danger"
            @click="deletePresetConfirmed"
            :disabled="deleteDialog.isDeleting"
          >
            <span v-if="deleteDialog.isDeleting">Deleting…</span>
            <span v-else>Delete</span>
          </button>
        </div>
      </div>
    </div>

    <div v-if="exportDialog.visible" class="modal-backdrop" @click.self="closeExportDialog">
      <div class="modal modal-wide">
        <header class="modal-header">
          <h2>Export SMB preset</h2>
          <button type="button" class="icon-button" @click="closeExportDialog" aria-label="Close dialog">
            <span aria-hidden="true">×</span>
          </button>
        </header>
        <p class="helper">Copy this JSON into the SMB input to apply the preset manually.</p>
        <textarea class="code-block" :value="exportDialog.json" rows="8" readonly></textarea>
        <div class="modal-actions">
          <button type="button" class="ghost" @click="closeExportDialog">Close</button>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue';
import {
  createSmbPreset,
  deleteSmbPreset,
  getSmbConfiguration,
  listEncodingRules,
  listSmbPresets,
  testSmbConfiguration,
  updateSmbConfiguration,
  updateSmbPreset
} from '../api/client.js';

const status = ref('');
const isSaving = ref(false);
const isTesting = ref(false);
const isSyncingPresets = ref(false);
const smbPresets = ref([]);
const isLoadingPresets = ref(false);

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

const presetDialog = reactive({
  visible: false,
  mode: 'create',
  isSaving: false,
  error: '',
  form: {
    id: null,
    name: '',
    description: '',
    shareUrl: '',
    username: '',
    password: '',
    inputPath: '',
    outputPath: ''
  }
});

const deleteDialog = reactive({
  visible: false,
  preset: null,
  isDeleting: false,
  error: ''
});

const exportDialog = reactive({
  visible: false,
  preset: null,
  json: ''
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

function maskPassword(value) {
  if (!value) {
    return '';
  }
  const maskedLength = Math.min(String(value).length, 12);
  return '•'.repeat(Math.max(maskedLength, 3));
}

function applyEncodingRules(rules) {
  if (Array.isArray(rules) && rules.length > 0) {
    form.presets.splice(0, form.presets.length, ...rules.map(mapRuleToPreset));
    return true;
  }
  form.presets.splice(0, form.presets.length, ...cloneDefaultPresets());
  return false;
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
    if (error?.status === 404) {
      status.value = 'No SMB configuration saved yet. Enter the share details to begin.';
    } else {
      console.warn('Unable to load SMB configuration', error);
      status.value = `Unable to load SMB configuration. ${parseErrorMessage(error)}`;
    }
  }
}

function buildSmbPayload() {
  return {
    share_url: form.smb.host.trim(),
    username: form.smb.username.trim(),
    password: form.smb.password,
    input_path: form.smb.input.trim(),
    output_path: form.smb.output.trim()
  };
}

function populatePresetDialogForm(preset) {
  if (preset) {
    presetDialog.form.id = preset.id ?? null;
    presetDialog.form.name = preset.name ?? '';
    presetDialog.form.description = preset.description ?? '';
    presetDialog.form.shareUrl = preset.share_url ?? '';
    presetDialog.form.username = preset.username ?? '';
    presetDialog.form.password = preset.password ?? '';
    presetDialog.form.inputPath = preset.input_path ?? '';
    presetDialog.form.outputPath = preset.output_path ?? '';
  } else {
    presetDialog.form.id = null;
    presetDialog.form.name = '';
    presetDialog.form.description = '';
    presetDialog.form.shareUrl = form.smb.host ?? '';
    presetDialog.form.username = form.smb.username ?? '';
    presetDialog.form.password = form.smb.password ?? '';
    presetDialog.form.inputPath = form.smb.input ?? '';
    presetDialog.form.outputPath = form.smb.output ?? '';
  }
}

function openCreatePresetDialog() {
  presetDialog.mode = 'create';
  presetDialog.error = '';
  presetDialog.isSaving = false;
  populatePresetDialogForm(null);
  presetDialog.visible = true;
}

function openEditPresetDialog(preset) {
  if (!preset) {
    return;
  }
  presetDialog.mode = 'edit';
  presetDialog.error = '';
  presetDialog.isSaving = false;
  populatePresetDialogForm(preset);
  presetDialog.visible = true;
}

function closePresetDialog() {
  if (presetDialog.isSaving) {
    return;
  }
  presetDialog.visible = false;
  presetDialog.error = '';
}

function buildPresetPayload() {
  const name = presetDialog.form.name.trim();
  const shareUrl = presetDialog.form.shareUrl.trim();
  const username = presetDialog.form.username.trim();
  const password = presetDialog.form.password;
  const inputPath = presetDialog.form.inputPath.trim();
  const outputPath = presetDialog.form.outputPath.trim();
  const description = presetDialog.form.description ? presetDialog.form.description.trim() : '';

  if (!name || !shareUrl || !username || !password || !inputPath || !outputPath) {
    presetDialog.error = 'Name, share URL, username, password, input path, and output path are required.';
    return null;
  }

  return {
    name,
    share_url: shareUrl,
    username,
    password,
    input_path: inputPath,
    output_path: outputPath,
    description: description || null
  };
}

async function submitPresetDialog() {
  if (presetDialog.isSaving) {
    return;
  }

  const payload = buildPresetPayload();
  if (!payload) {
    return;
  }

  presetDialog.isSaving = true;
  try {
    if (presetDialog.mode === 'create') {
      const saved = await createSmbPreset(payload);
      status.value = `Preset "${saved.name}" created successfully.`;
    } else if (presetDialog.form.id != null) {
      const saved = await updateSmbPreset(presetDialog.form.id, payload);
      status.value = `Preset "${saved.name}" updated successfully.`;
    }
    await refreshSmbPresets({ silent: true });
    presetDialog.visible = false;
    presetDialog.error = '';
  } catch (error) {
    console.warn('Unable to save SMB preset', error);
    presetDialog.error = parseErrorMessage(error);
  } finally {
    presetDialog.isSaving = false;
  }
}

async function refreshSmbPresets(options = {}) {
  const silent = options && typeof options === 'object' && 'silent' in options ? Boolean(options.silent) : false;
  if (isLoadingPresets.value) {
    return false;
  }
  isLoadingPresets.value = true;
  try {
    const presets = await listSmbPresets();
    const normalized = Array.isArray(presets) ? presets : [];
    smbPresets.value.splice(0, smbPresets.value.length, ...normalized);
    if (!silent) {
      status.value = normalized.length
        ? 'Loaded SMB presets from the backend.'
        : 'No SMB presets saved yet. Create one to reuse common settings.';
    }
    return true;
  } catch (error) {
    console.warn('Unable to load SMB presets', error);
    smbPresets.value.splice(0, smbPresets.value.length);
    if (!silent) {
      status.value = `Unable to load SMB presets. ${parseErrorMessage(error)}`;
    }
    return false;
  } finally {
    isLoadingPresets.value = false;
  }
}

function confirmDeletePreset(preset) {
  deleteDialog.preset = preset ?? null;
  deleteDialog.error = '';
  deleteDialog.isDeleting = false;
  if (deleteDialog.preset) {
    deleteDialog.visible = true;
  }
}

function closeDeleteDialog() {
  if (deleteDialog.isDeleting) {
    return;
  }
  deleteDialog.visible = false;
  deleteDialog.preset = null;
  deleteDialog.error = '';
}

async function deletePresetConfirmed() {
  if (!deleteDialog.preset || deleteDialog.isDeleting) {
    return;
  }

  deleteDialog.isDeleting = true;
  const presetId = deleteDialog.preset.id;
  const presetName = deleteDialog.preset.name;
  try {
    await deleteSmbPreset(presetId);
    status.value = `Preset "${presetName}" deleted.`;
    deleteDialog.visible = false;
    deleteDialog.preset = null;
    deleteDialog.error = '';
    await refreshSmbPresets({ silent: true });
  } catch (error) {
    console.warn('Unable to delete SMB preset', error);
    deleteDialog.error = parseErrorMessage(error);
  } finally {
    deleteDialog.isDeleting = false;
  }
}

function openExportDialog(preset) {
  if (!preset) {
    return;
  }
  exportDialog.preset = preset;
  exportDialog.json = JSON.stringify(
    {
      share_url: preset.share_url ?? '',
      username: preset.username ?? '',
      password: preset.password ?? '',
      input_path: preset.input_path ?? '',
      output_path: preset.output_path ?? ''
    },
    null,
    2
  );
  exportDialog.visible = true;
}

function closeExportDialog() {
  exportDialog.visible = false;
  exportDialog.preset = null;
  exportDialog.json = '';
}

function applyPreset(preset) {
  if (!preset) {
    return;
  }
  form.smb.host = preset.share_url ?? '';
  form.smb.username = preset.username ?? '';
  form.smb.password = preset.password ?? '';
  form.smb.input = preset.input_path ?? '';
  form.smb.output = preset.output_path ?? '';
  status.value = `Preset "${preset.name}" applied to the SMB form.`;
}

function parseErrorMessage(error) {
  if (!error) {
    return 'Unexpected error.';
  }
  if (typeof error.body === 'string') {
    try {
      const parsed = JSON.parse(error.body);
      if (parsed && typeof parsed.detail === 'string') {
        return parsed.detail;
      }
      if (typeof parsed === 'string') {
        return parsed;
      }
    } catch (parseError) {
      return error.body;
    }
  }
  if (error.message) {
    return error.message;
  }
  return 'Unexpected error.';
}

async function saveConfiguration() {
  if (isSaving.value) {
    return;
  }
  const payload = buildSmbPayload();
  isSaving.value = true;
  status.value = 'Saving SMB configuration...';
  try {
    const saved = await updateSmbConfiguration(payload);
    form.smb.host = saved.share_url ?? payload.share_url;
    form.smb.username = saved.username ?? payload.username;
    form.smb.password = saved.password ?? payload.password;
    form.smb.input = saved.input_path ?? payload.input_path;
    form.smb.output = saved.output_path ?? payload.output_path;
    status.value = 'SMB configuration saved successfully.';
    await refreshEncodingRules({ silent: true });
  } catch (error) {
    console.warn('Unable to save SMB configuration', error);
    status.value = `Failed to save SMB configuration. ${parseErrorMessage(error)}`;
  } finally {
    isSaving.value = false;
  }
}

async function testConnection() {
  if (isTesting.value) {
    return;
  }
  const payload = buildSmbPayload();
  isTesting.value = true;
  status.value = 'Testing SMB configuration...';
  try {
    const result = await testSmbConfiguration(payload);
    const latencyValue = Number(result.latency_ms);
    const latencyNote = Number.isFinite(latencyValue) ? ` (Latency: ${latencyValue.toFixed(2)} ms)` : '';
    status.value = `${result.message}${latencyNote}`;
  } catch (error) {
    console.warn('Unable to test SMB configuration', error);
    status.value = `Unable to test SMB configuration. ${parseErrorMessage(error)}`;
  } finally {
    isTesting.value = false;
  }
}

async function refreshEncodingRules(options = {}) {
  const silent = options && typeof options === 'object' && 'silent' in options ? Boolean(options.silent) : false;
  if (isSyncingPresets.value) {
    return false;
  }
  isSyncingPresets.value = true;
  try {
    const rules = await listEncodingRules();
    const hasRules = applyEncodingRules(rules);
    if (!silent) {
      status.value = hasRules
        ? 'Live encoding rules synced from the backend API.'
        : 'No encoding rules returned by the backend API. Showing default presets.';
    }
    return hasRules;
  } catch (error) {
    console.warn('Unable to load encoding rules', error);
    form.presets.splice(0, form.presets.length, ...cloneDefaultPresets());
    status.value = 'Unable to load encoding rules. Showing default presets. Check backend connectivity.';
    return false;
  } finally {
    isSyncingPresets.value = false;
  }
}

onMounted(() => {
  void loadSmbConfiguration();
  void refreshSmbPresets({ silent: true });
  void (async () => {
    const hasRules = await refreshEncodingRules({ silent: true });
    if (!hasRules && !status.value) {
      status.value = 'No encoding rules configured yet.';
    }
  })();
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

.actions {
  display: flex;
  gap: 0.75rem;
  align-items: center;
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

.ghost {
  border: 1px solid rgba(148, 163, 184, 0.4);
  background: white;
  color: #111826;
  padding: 0.65rem 1.25rem;
  border-radius: 999px;
  font-weight: 600;
  cursor: pointer;
}

.ghost:disabled,
.save:disabled {
  opacity: 0.6;
  cursor: not-allowed;
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

textarea {
  border-radius: 0.75rem;
  border: 1px solid rgba(148, 163, 184, 0.5);
  padding: 0.75rem 1rem;
  font-size: 1rem;
  resize: vertical;
  min-height: 4rem;
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

.panel-heading {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
}

.panel-heading p {
  margin: 0;
  color: #475569;
  font-size: 0.9rem;
}

.preset-toolbar {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.preset-toolbar .ghost:last-child {
  border: none;
  background: #111826;
  color: white;
}

.preset-toolbar .ghost:last-child:hover {
  background: #0f172a;
}

.smb-presets {
  align-content: start;
  gap: 1.25rem;
}

.smb-preset-card {
  border: 1px solid rgba(226, 232, 240, 0.8);
  border-radius: 1.25rem;
  padding: 1.5rem;
  display: grid;
  gap: 1rem;
}

.smb-preset-card header {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: flex-start;
}

.smb-preset-card h3 {
  margin: 0 0 0.3rem;
}

.smb-preset-card p {
  margin: 0;
  color: #475569;
}

.smb-preset-card dl {
  display: grid;
  gap: 0.75rem;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  margin: 0;
}

.preset-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.icon-button {
  border: none;
  background: transparent;
  border-radius: 999px;
  padding: 0.4rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #475569;
  cursor: pointer;
}

.icon-button:hover {
  background: rgba(148, 163, 184, 0.25);
  color: #111826;
}

.ghost.danger {
  border-color: rgba(248, 113, 113, 0.5);
  color: #b91c1c;
}

.ghost.danger:hover {
  border-color: rgba(248, 113, 113, 0.8);
  color: #991b1b;
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

.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.55);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1.5rem;
  z-index: 100;
}

.modal {
  background: white;
  border-radius: 1.25rem;
  padding: 1.5rem;
  display: grid;
  gap: 1.25rem;
  width: min(100%, 520px);
  box-shadow: 0 30px 60px rgba(15, 23, 42, 0.25);
}

.modal-wide {
  width: min(100%, 640px);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
}

.modal-header h2 {
  margin: 0;
}

.modal-body {
  display: grid;
  gap: 1rem;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
}

.code-block {
  font-family: 'SFMono-Regular', Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace;
  background: rgba(148, 163, 184, 0.12);
  border: 1px solid rgba(148, 163, 184, 0.5);
  border-radius: 0.75rem;
  padding: 1rem;
  font-size: 0.9rem;
  white-space: pre;
}

.form-error {
  margin: 0;
  color: #b91c1c;
  font-size: 0.9rem;
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
