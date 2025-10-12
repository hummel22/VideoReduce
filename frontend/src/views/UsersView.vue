<template>
  <section class="users-view">
    <header class="header">
      <div>
        <h1>Users</h1>
        <p>Generate API tokens for operators and devices that interact with the backend.</p>
      </div>
      <form class="add-user" @submit.prevent="addUser">
        <label class="sr-only" for="user-name">User name</label>
        <input
          id="user-name"
          v-model="newUserName"
          type="text"
          name="user-name"
          autocomplete="off"
          placeholder="Camera 12"
        />
        <button type="submit" :disabled="isSubmitting">
          {{ isSubmitting ? 'Generating…' : 'Generate token' }}
        </button>
      </form>
    </header>

    <section class="panel">
      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th>Token</th>
            <th>Date created</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in users" :key="user.id">
            <td>{{ user.name }}</td>
            <td>
              <code class="token">{{ user.token }}</code>
            </td>
            <td>{{ user.createdAt }}</td>
          </tr>
          <tr v-if="users.length === 0">
            <td colspan="3" class="empty">No user tokens generated yet.</td>
          </tr>
        </tbody>
      </table>
    </section>

    <p v-if="statusMessage" class="banner">{{ statusMessage }}</p>
  </section>
</template>

<script setup>
import { onMounted, ref } from 'vue';
import { createUser, listUsers } from '../api/client.js';

const users = ref([]);
const newUserName = ref('');
const statusMessage = ref('');
const isSubmitting = ref(false);

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

function mapUser(user) {
  return {
    id: user.id,
    name: user.username,
    token: user.token,
    createdAt: formatTimestamp(user.created_at)
  };
}

async function loadUsers() {
  try {
    const response = await listUsers();
    if (Array.isArray(response)) {
      users.value = response.map(mapUser);
      statusMessage.value = '';
    }
  } catch (error) {
    console.warn('Unable to load users', error);
    users.value = [];
    statusMessage.value = 'Unable to load users. Ensure the backend is reachable.';
  }
}

async function addUser() {
  const username = newUserName.value.trim();
  if (!username) {
    statusMessage.value = 'Enter a name before generating a token.';
    return;
  }

  isSubmitting.value = true;
  statusMessage.value = '';
  try {
    const response = await createUser({ username });
    const mapped = mapUser(response);
    users.value = [mapped, ...users.value];
    statusMessage.value = `Generated a token for ${mapped.name}.`;
    newUserName.value = '';
  } catch (error) {
    console.warn('Unable to create user', error);
    statusMessage.value = 'Failed to generate a token. Try again.';
  } finally {
    isSubmitting.value = false;
  }
}

onMounted(loadUsers);
</script>

<style scoped>
.users-view {
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

.add-user {
  display: flex;
  gap: 0.75rem;
  align-items: center;
}

.add-user input {
  border-radius: 0.85rem;
  border: 1px solid rgba(148, 163, 184, 0.5);
  padding: 0.65rem 1rem;
  font-size: 1rem;
  min-width: 200px;
}

.add-user button {
  border: none;
  background: linear-gradient(135deg, #2563eb, #0ea5e9);
  color: white;
  padding: 0.65rem 1.4rem;
  border-radius: 999px;
  font-weight: 600;
  cursor: pointer;
  box-shadow: 0 12px 24px rgba(14, 165, 233, 0.35);
}

.add-user button[disabled] {
  opacity: 0.7;
  cursor: not-allowed;
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

.panel {
  background: white;
  border-radius: 1.5rem;
  box-shadow: 0 18px 45px rgba(15, 23, 42, 0.05);
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th,
td {
  padding: 1rem 1.5rem;
  border-bottom: 1px solid rgba(226, 232, 240, 0.6);
  text-align: left;
}

th {
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-size: 0.8rem;
  color: #94a3b8;
}

tr:last-child td {
  border-bottom: none;
}

.token {
  background: rgba(226, 232, 240, 0.6);
  padding: 0.35rem 0.65rem;
  border-radius: 0.5rem;
  display: inline-block;
  font-family: 'Fira Mono', 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
  font-size: 0.9rem;
}

.empty {
  text-align: center;
  color: #94a3b8;
}

.banner {
  margin: 0;
  background: rgba(147, 197, 253, 0.2);
  color: #1d4ed8;
  border-radius: 1rem;
  padding: 0.9rem 1.2rem;
}

@media (max-width: 720px) {
  .header {
    flex-direction: column;
    align-items: stretch;
    gap: 1rem;
  }

  .add-user {
    width: 100%;
    flex-direction: column;
    align-items: stretch;
  }

  .add-user input,
  .add-user button {
    width: 100%;
  }
}
</style>
