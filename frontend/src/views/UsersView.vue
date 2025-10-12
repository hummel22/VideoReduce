<template>
  <section class="users-view">
    <header class="header">
      <div>
        <h1>Administrators</h1>
        <p>Manage who can access the dashboard, queue controls, and encoding presets.</p>
      </div>
      <button type="button" class="invite" @click="addUser">
        Invite admin
      </button>
    </header>

    <section class="panel">
      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th>Email</th>
            <th>Role</th>
            <th>Last login</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in users" :key="user.email">
            <td>{{ user.name }}</td>
            <td>{{ user.email }}</td>
            <td>
              <span class="role" :class="roleClass(user.role)">{{ user.role }}</span>
            </td>
            <td>{{ user.lastLogin }}</td>
          </tr>
        </tbody>
      </table>
    </section>

    <p v-if="banner" class="banner">{{ banner }}</p>
  </section>
</template>

<script setup>
import { reactive, ref } from 'vue';

const users = reactive([
  {
    name: 'Avery Cole',
    email: 'avery.cole@example.com',
    role: 'Owner',
    lastLogin: 'Just now'
  },
  {
    name: 'Jordan Fox',
    email: 'jordan.fox@example.com',
    role: 'Admin',
    lastLogin: '23 minutes ago'
  },
  {
    name: 'Kai Martin',
    email: 'kai.martin@example.com',
    role: 'Reviewer',
    lastLogin: 'Yesterday'
  }
]);

const banner = ref('');

function addUser() {
  banner.value = 'Invite flow coming soon. Use the backend CLI to provision administrators in the meantime.';
}

function roleClass(role) {
  switch (role) {
    case 'Owner':
      return 'role-owner';
    case 'Admin':
      return 'role-admin';
    default:
      return 'role-reviewer';
  }
}
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

.invite {
  border: none;
  background: linear-gradient(135deg, #8b5cf6, #6366f1);
  color: white;
  padding: 0.65rem 1.5rem;
  border-radius: 999px;
  font-weight: 600;
  cursor: pointer;
  box-shadow: 0 12px 24px rgba(99, 102, 241, 0.35);
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

.role {
  padding: 0.35rem 0.75rem;
  border-radius: 999px;
  font-weight: 600;
  font-size: 0.85rem;
}

.role-owner {
  background: rgba(99, 102, 241, 0.18);
  color: #4338ca;
}

.role-admin {
  background: rgba(34, 197, 94, 0.18);
  color: #166534;
}

.role-reviewer {
  background: rgba(251, 191, 36, 0.18);
  color: #92400e;
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

  .invite {
    width: 100%;
  }
}
</style>
