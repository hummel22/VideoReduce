import { createApp, ref, reactive, computed, onMounted } from 'https://unpkg.com/vue@3.4.21/dist/vue.esm-browser.prod.js';
import PrimeVue from 'https://unpkg.com/primevue@3.53.0/config/config.esm.js';
import ToastService from 'https://unpkg.com/primevue@3.53.0/toastservice/toastservice.esm.js';
import { useToast } from 'https://unpkg.com/primevue@3.53.0/usetoast/usetoast.esm.js';
import Button from 'https://unpkg.com/primevue@3.53.0/button/button.esm.js';
import Card from 'https://unpkg.com/primevue@3.53.0/card/card.esm.js';
import InputText from 'https://unpkg.com/primevue@3.53.0/inputtext/inputtext.esm.js';
import Password from 'https://unpkg.com/primevue@3.53.0/password/password.esm.js';
import Textarea from 'https://unpkg.com/primevue@3.53.0/textarea/textarea.esm.js';
import DataTable from 'https://unpkg.com/primevue@3.53.0/datatable/datatable.esm.js';
import Column from 'https://unpkg.com/primevue@3.53.0/column/column.esm.js';
import Tag from 'https://unpkg.com/primevue@3.53.0/tag/tag.esm.js';
import Toast from 'https://unpkg.com/primevue@3.53.0/toast/toast.esm.js';

const STORAGE_KEY = 'videoreduce_admin_token';

async function parseError(response, fallbackMessage) {
  try {
    const payload = await response.json();
    if (!payload) {
      return fallbackMessage;
    }
    if (typeof payload === 'string') {
      return payload;
    }
    if (payload.detail) {
      if (typeof payload.detail === 'string') {
        return payload.detail;
      }
      if (Array.isArray(payload.detail)) {
        return payload.detail.map((item) => item.msg ?? item).join(', ');
      }
      if (typeof payload.detail === 'object') {
        return Object.values(payload.detail).join(', ');
      }
    }
    return fallbackMessage;
  } catch (error) {
    return fallbackMessage;
  }
}

const App = {
  name: 'AdminApp',
  setup() {
    const toast = useToast();
    const authToken = ref(localStorage.getItem(STORAGE_KEY) ?? '');
    const loginForm = reactive({ username: '', password: '' });
    const loginLoading = ref(false);
    const tokens = ref([]);
    const tokensLoading = ref(false);
    const createForm = reactive({ username: '', description: '' });
    const createLoading = ref(false);
    const actionLoading = ref(null);
    const issuedToken = ref('');

    const isAuthenticated = computed(() => Boolean(authToken.value));

    const resetIssuedToken = () => {
      issuedToken.value = '';
    };

    const logout = (message) => {
      authToken.value = '';
      localStorage.removeItem(STORAGE_KEY);
      tokens.value = [];
      resetIssuedToken();
      if (message) {
        toast.add({ severity: 'warn', summary: 'Signed out', detail: message, life: 4000 });
      }
    };

    const authorizedFetch = async (url, options = {}) => {
      const headers = new Headers(options.headers ?? {});
      if (!headers.has('Accept')) {
        headers.set('Accept', 'application/json');
      }
      if (options.body && !headers.has('Content-Type')) {
        headers.set('Content-Type', 'application/json');
      }
      if (authToken.value) {
        headers.set('Authorization', `Bearer ${authToken.value}`);
      }
      return fetch(url, { ...options, headers });
    };

    const fetchTokens = async () => {
      if (!authToken.value) {
        return;
      }
      tokensLoading.value = true;
      try {
        const response = await authorizedFetch('/admin/tokens');
        if (response.ok) {
          tokens.value = await response.json();
        } else if (response.status === 401) {
          logout('Your session expired. Please log in again.');
        } else {
          const detail = await parseError(response, 'Unable to load API tokens.');
          toast.add({ severity: 'error', summary: 'Load failed', detail, life: 5000 });
        }
      } catch (error) {
        toast.add({ severity: 'error', summary: 'Network error', detail: error.message, life: 5000 });
      } finally {
        tokensLoading.value = false;
      }
    };

    const login = async () => {
      resetIssuedToken();
      loginLoading.value = true;
      try {
        const response = await fetch('/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
          body: JSON.stringify({ username: loginForm.username, password: loginForm.password }),
        });
        if (!response.ok) {
          const detail = await parseError(response, 'Unable to authenticate with the provided credentials.');
          toast.add({ severity: 'error', summary: 'Login failed', detail, life: 5000 });
          return;
        }
        const payload = await response.json();
        authToken.value = payload.access_token;
        localStorage.setItem(STORAGE_KEY, payload.access_token);
        toast.add({ severity: 'success', summary: 'Login successful', detail: 'Session established.', life: 2500 });
        await fetchTokens();
      } catch (error) {
        toast.add({ severity: 'error', summary: 'Network error', detail: error.message, life: 5000 });
      } finally {
        loginLoading.value = false;
      }
    };

    const createToken = async () => {
      resetIssuedToken();
      if (!createForm.username.trim()) {
        toast.add({ severity: 'warn', summary: 'Missing username', detail: 'Provide a username before issuing a token.', life: 4000 });
        return;
      }
      createLoading.value = true;
      try {
        const response = await authorizedFetch('/admin/tokens', {
          method: 'POST',
          body: JSON.stringify({
            username: createForm.username.trim(),
            description: createForm.description.trim() || undefined,
          }),
        });
        if (!response.ok) {
          if (response.status === 401) {
            logout('Your session expired. Please log in again.');
            return;
          }
          const detail = await parseError(response, 'Unable to create API token.');
          toast.add({ severity: 'error', summary: 'Creation failed', detail, life: 5000 });
          return;
        }
        const payload = await response.json();
        issuedToken.value = payload.token;
        toast.add({ severity: 'success', summary: 'Token created', detail: 'Copy the token below before leaving this page.', life: 5000 });
        createForm.username = '';
        createForm.description = '';
        await fetchTokens();
      } catch (error) {
        toast.add({ severity: 'error', summary: 'Network error', detail: error.message, life: 5000 });
      } finally {
        createLoading.value = false;
      }
    };

    const revokeToken = async (tokenId) => {
      actionLoading.value = tokenId;
      try {
        const response = await authorizedFetch(`/admin/tokens/${tokenId}`, { method: 'DELETE' });
        if (response.status === 204) {
          tokens.value = tokens.value.filter((item) => item.id !== tokenId);
          toast.add({ severity: 'success', summary: 'Token revoked', detail: 'The API token has been revoked.', life: 3000 });
        } else if (response.status === 401) {
          logout('Your session expired. Please log in again.');
        } else {
          const detail = await parseError(response, 'Unable to revoke the token.');
          toast.add({ severity: 'error', summary: 'Revoke failed', detail, life: 5000 });
        }
      } catch (error) {
        toast.add({ severity: 'error', summary: 'Network error', detail: error.message, life: 5000 });
      } finally {
        actionLoading.value = null;
      }
    };

    onMounted(async () => {
      if (authToken.value) {
        await fetchTokens();
      }
    });

    return {
      loginForm,
      loginLoading,
      login,
      createForm,
      createLoading,
      createToken,
      tokens,
      tokensLoading,
      revokeToken,
      actionLoading,
      issuedToken,
      isAuthenticated,
      logout,
      parseRole(role) {
        return role ? role.charAt(0).toUpperCase() + role.slice(1) : '';
      },
    };
  },
  template: `
    <div class="admin-shell">
      <Toast />
      <header class="admin-header">
        <h1>VideoReduce Admin Panel</h1>
        <Button
          v-if="isAuthenticated"
          label="Sign out"
          icon="pi pi-sign-out"
          class="p-button-text"
          @click="logout()"
        />
      </header>

      <section v-if="!isAuthenticated" class="login-card">
        <Card>
          <template #title>Administrator Login</template>
          <template #content>
            <div class="p-fluid p-formgrid p-grid" style="display: grid; gap: 1rem;">
              <span class="p-input-icon-left">
                <i class="pi pi-user" />
                <InputText
                  v-model="loginForm.username"
                  placeholder="Username"
                  autocomplete="username"
                />
              </span>
              <Password
                v-model="loginForm.password"
                placeholder="Password"
                toggle-mask
                :feedback="false"
                :input-props="{ autocomplete: 'current-password' }"
              />
              <Button
                label="Log in"
                icon="pi pi-lock-open"
                :loading="loginLoading"
                @click="login"
              />
            </div>
          </template>
        </Card>
      </section>

      <section v-else class="token-layout">
        <Card>
          <template #title>Issue mobile API tokens</template>
          <template #content>
            <div class="p-fluid" style="display: grid; gap: 1rem;">
              <div class="p-field">
                <label for="token-username" class="p-d-block">Username</label>
                <InputText
                  id="token-username"
                  v-model="createForm.username"
                  placeholder="mobile-user"
                  autocomplete="off"
                />
              </div>
              <div class="p-field">
                <label for="token-description" class="p-d-block">Description</label>
                <Textarea
                  id="token-description"
                  v-model="createForm.description"
                  auto-resize
                  rows="3"
                  placeholder="Purpose or device notes"
                />
              </div>
              <div class="create-token-footer">
                <Button
                  label="Issue token"
                  icon="pi pi-key"
                  :loading="createLoading"
                  @click="createToken"
                />
                <div v-if="issuedToken" class="issued-token">
                  <i class="pi pi-info-circle" style="font-size: 1.25rem; color: #4338ca;"></i>
                  <div>
                    <p style="margin: 0 0 0.5rem; font-weight: 600;">Copy this token before leaving the page.</p>
                    <code>{{ issuedToken }}</code>
                  </div>
                </div>
              </div>
            </div>
          </template>
        </Card>

        <Card class="token-table">
          <template #title>Active tokens</template>
          <template #content>
            <DataTable
              :value="tokens"
              :loading="tokensLoading"
              responsive-layout="scroll"
              size="small"
              data-key="id"
              empty-message="No API tokens have been issued yet."
            >
              <Column field="id" header="ID" style="width: 6rem"></Column>
              <Column header="User">
                <template #body="{ data }">
                  <div class="token-meta">
                    <span>{{ data.user?.username }}</span>
                    <Tag :value="parseRole(data.user?.role)" severity="info"></Tag>
                  </div>
                </template>
              </Column>
              <Column field="description" header="Description"></Column>
              <Column header="Token">
                <template #body="{ data }">
                  <span class="token-value">{{ data.token }}</span>
                </template>
              </Column>
              <Column header="">
                <template #body="{ data }">
                  <Button
                    icon="pi pi-trash"
                    class="p-button-rounded p-button-text p-button-danger"
                    :loading="actionLoading === data.id"
                    @click="revokeToken(data.id)"
                  />
                </template>
              </Column>
            </DataTable>
          </template>
        </Card>
      </section>
    </div>
  `,
};

const app = createApp(App);
app.use(PrimeVue, { ripple: true });
app.use(ToastService);
app.component('Button', Button);
app.component('Card', Card);
app.component('InputText', InputText);
app.component('Password', Password);
app.component('Textarea', Textarea);
app.component('DataTable', DataTable);
app.component('Column', Column);
app.component('Tag', Tag);
app.component('Toast', Toast);
app.mount('#app');
