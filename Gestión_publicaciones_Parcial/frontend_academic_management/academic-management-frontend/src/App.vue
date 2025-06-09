<template>
  <div class="container">
    <!-- Login Form -->
    <div v-if="!isAuthenticated" class="login-form">
      <h2 style="text-align: center; margin-bottom: 20px;">Iniciar Sesión</h2>
      
      <div v-if="loginError" class="alert alert-error">
        {{ loginError }}
      </div>
      
      <div class="form-group">
        <label>Usuario:</label>
        <input 
          type="text" 
          v-model="credentials.username" 
          @keyup.enter="login"
          placeholder="Ingrese su usuario"
        >
      </div>
      
      <div class="form-group">
        <label>Contraseña:</label>
        <input 
          type="password" 
          v-model="credentials.password" 
          @keyup.enter="login"
          placeholder="Ingrese su contraseña"
        >
      </div>
      
      <button class="btn btn-success" @click="login" :disabled="loading">
        {{ loading ? 'Ingresando...' : 'Ingresar' }}
      </button>
    </div>

    <!-- Main App -->
    <div v-else>
      <div class="header">
        <h1>Gestión Académica - CRUD</h1>
        <div class="user-info">
          Bienvenido, {{ user.username }}
          <button class="logout-btn" @click="logout">Salir</button>
        </div>
      </div>
      
      <div class="tabs">
        <div 
          class="tab" 
          :class="{ active: activeTab === 'countries' }" 
          @click="changeTab('countries')"
        >
          Países
        </div>
        <div 
          class="tab" 
          :class="{ active: activeTab === 'keywords' }" 
          @click="changeTab('keywords')"
        >
          Palabras Clave
        </div>
        <div 
          class="tab" 
          :class="{ active: activeTab === 'publication-types' }" 
          @click="changeTab('publication-types')"
        >
          Tipos de Publicación
        </div>
      </div>
      
      <div class="content">
        <div v-if="message" :class="'alert ' + (messageType === 'success' ? 'alert-success' : 'alert-error')">
          {{ message }}
        </div>
        
        <!-- Dynamic Component -->
        <component 
          :is="currentComponent" 
          :items="items"
          :loading="loading"
          :current-page="currentPage"
          :total-pages="totalPages"
          @create="openModal('create')"
          @edit="openModal('edit', $event)"
          @delete="deleteItem"
          @search="handleSearch"
          @page-change="changePage"
        />
      </div>
    </div>
    
    <!-- Modal -->
    <div v-if="showModal" class="modal" @click.self="closeModal">
      <div class="modal-content">
        <div class="modal-header">
          <h3>{{ modalTitle }}</h3>
          <span class="close" @click="closeModal">&times;</span>
        </div>
        
        <form @submit.prevent="saveItem">
          <!-- Countries Form -->
          <div v-if="activeTab === 'countries'">
            <div class="form-group">
              <label>Nombre:</label>
              <input type="text" v-model="form.name" required>
            </div>
            <div class="form-group">
              <label>Código (2 letras):</label>
              <input type="text" v-model="form.code" maxlength="2" required>
            </div>
          </div>
          
          <!-- Keywords Form -->
          <div v-if="activeTab === 'keywords'">
            <div class="form-group">
              <label>Nombre:</label>
              <input type="text" v-model="form.name" required>
            </div>
          </div>
          
          <!-- Publication Types Form -->
          <div v-if="activeTab === 'publication-types'">
            <div class="form-group">
              <label>Nombre:</label>
              <input type="text" v-model="form.name" required>
            </div>
            <div class="form-group">
              <label>Descripción:</label>
              <textarea v-model="form.description" required></textarea>
            </div>
          </div>
          
          <div style="margin-top: 20px;">
            <button type="submit" class="btn btn-success" :disabled="loading">
              {{ loading ? 'Guardando...' : 'Guardar' }}
            </button>
            <button type="button" class="btn btn-secondary" @click="closeModal">
              Cancelar
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script>
import apiService from './services/api'
import CountriesTable from './components/CountriesTable.vue'
import KeywordsTable from './components/KeywordsTable.vue'
import PublicationTypesTable from './components/PublicationTypesTable.vue'

export default {
  name: 'App',
  components: {
    CountriesTable,
    KeywordsTable,
    PublicationTypesTable
  },
  data() {
    return {
      // Authentication
      isAuthenticated: false,
      user: JSON.parse(localStorage.getItem('user') || '{}'),
      credentials: {
        username: '',
        password: ''
      },
      loginError: '',
      
      // UI State
      activeTab: 'countries',
      showModal: false,
      modalMode: 'create',
      loading: false,
      message: '',
      messageType: 'success',
      
      // Data
      items: [],
      form: {},
      searchTerm: '',
      currentPage: 1,
      totalPages: 1
    }
  },
  
  computed: {
    modalTitle() {
      const labels = {
        'countries': 'País',
        'keywords': 'Palabra Clave',
        'publication-types': 'Tipo de Publicación'
      };
      return this.modalMode === 'create' 
        ? `Crear ${labels[this.activeTab]}` 
        : `Editar ${labels[this.activeTab]}`;
    },
    currentComponent() {
      const components = {
        'countries': 'CountriesTable',
        'keywords': 'KeywordsTable',
        'publication-types': 'PublicationTypesTable'
      };
      return components[this.activeTab];
    }
  },
  
  mounted() {
    this.checkAuth();
  },
  
  methods: {
    // Authentication
    checkAuth() {
      const token = localStorage.getItem('token');
      if (token && this.user.username) {
        this.isAuthenticated = true;
        this.loadItems();
      }
    },
    
    async login() {
      try {
        this.loading = true;
        this.loginError = '';
        
        const { user } = await apiService.login(this.credentials);
        this.user = user;
        this.isAuthenticated = true;
        this.loadItems();
        
      } catch (error) {
        this.loginError = error.message;
      } finally {
        this.loading = false;
      }
    },
    
    logout() {
      apiService.logout();
      this.isAuthenticated = false;
      this.user = {};
      this.credentials = { username: '', password: '' };
    },
    
    // Tab Management
    changeTab(tab) {
      this.activeTab = tab;
      this.searchTerm = '';
      this.currentPage = 1;
      this.loadItems();
    },
    
    // CRUD Operations
    async loadItems() {
      try {
        this.loading = true;
        const params = {
          page: this.currentPage,
          per_page: 10,
          search: this.searchTerm
        };
        
        let response;
        switch (this.activeTab) {
          case 'countries':
            response = await apiService.getCountries(params);
            break;
          case 'keywords':
            response = await apiService.getKeywords(params);
            break;
          case 'publication-types':
            response = await apiService.getPublicationTypes(params);
            break;
        }
        
        this.items = response.data;
        this.totalPages = response.pages;
        
      } catch (error) {
        this.showMessage(error.message, 'error');
      } finally {
        this.loading = false;
      }
    },
    
    async saveItem() {
      try {
        this.loading = true;
        
        if (this.modalMode === 'create') {
          switch (this.activeTab) {
            case 'countries':
              await apiService.createCountry(this.form);
              break;
            case 'keywords':
              await apiService.createKeyword(this.form);
              break;
            case 'publication-types':
              await apiService.createPublicationType(this.form);
              break;
          }
          this.showMessage('Elemento creado exitosamente');
        } else {
          switch (this.activeTab) {
            case 'countries':
              await apiService.updateCountry(this.form.id, this.form);
              break;
            case 'keywords':
              await apiService.updateKeyword(this.form.id, this.form);
              break;
            case 'publication-types':
              await apiService.updatePublicationType(this.form.id, this.form);
              break;
          }
          this.showMessage('Elemento actualizado exitosamente');
        }
        
        this.closeModal();
        this.loadItems();
        
      } catch (error) {
        this.showMessage(error.message, 'error');
      } finally {
        this.loading = false;
      }
    },
    
    async deleteItem(id) {
      if (!confirm('¿Está seguro de que desea eliminar este elemento?')) {
        return;
      }
      
      try {
        switch (this.activeTab) {
          case 'countries':
            await apiService.deleteCountry(id);
            break;
          case 'keywords':
            await apiService.deleteKeyword(id);
            break;
          case 'publication-types':
            await apiService.deletePublicationType(id);
            break;
        }
        
        this.showMessage('Elemento eliminado exitosamente');
        this.loadItems();
        
      } catch (error) {
        this.showMessage(error.message, 'error');
      }
    },
    
    // Modal Management
    openModal(mode, item = null) {
      this.modalMode = mode;
      this.showModal = true;
      
      if (mode === 'create') {
        this.form = {};
      } else {
        this.form = { ...item };
      }
    },
    
    closeModal() {
      this.showModal = false;
      this.form = {};
    },
    
    // Event Handlers
    handleSearch(searchTerm) {
      this.searchTerm = searchTerm;
      this.currentPage = 1;
      this.loadItems();
    },
    
    changePage(page) {
      if (page >= 1 && page <= this.totalPages) {
        this.currentPage = page;
        this.loadItems();
      }
    },
    
    // Utility
    showMessage(message, type = 'success') {
      this.message = message;
      this.messageType = type;
      setTimeout(() => {
        this.message = '';
      }, 3000);
    }
  }
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: Arial, sans-serif;
  background-color: #f5f5f5;
  padding: 20px;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
  overflow: hidden;
}

.header {
  background: #2c3e50;
  color: white;
  padding: 20px;
  text-align: center;
}

.tabs {
  display: flex;
  background: #34495e;
}

.tab {
  flex: 1;
  padding: 15px;
  text-align: center;
  color: white;
  cursor: pointer;
  transition: background 0.3s;
}

.tab:hover {
  background: #2c3e50;
}

.tab.active {
  background: #3498db;
}

.content {
  padding: 20px;
}

.login-form {
  max-width: 400px;
  margin: 0 auto;
  padding: 30px;
  background: #f8f9fa;
  border-radius: 8px;
}

.form-group {
  margin-bottom: 15px;
}

label {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
  color: #333;
}

input, textarea, select {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

textarea {
  height: 80px;
  resize: vertical;
}

.btn {
  background: #3498db;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 4px;
  cursor: pointer;
  margin-right: 10px;
  margin-bottom: 10px;
}

.btn:hover {
  background: #2980b9;
}

.btn-success {
  background: #27ae60;
}

.btn-success:hover {
  background: #229954;
}

.btn-danger {
  background: #e74c3c;
}

.btn-danger:hover {
  background: #c0392b;
}

.btn-secondary {
  background: #6c757d;
}

.btn-secondary:hover {
  background: #5a6268;
}

.modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0,0,0,0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  padding: 30px;
  border-radius: 8px;
  max-width: 500px;
  width: 90%;
  max-height: 80vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 1px solid #ddd;
}

.close {
  cursor: pointer;
  font-size: 24px;
  color: #999;
}

.close:hover {
  color: #333;
}

.alert {
  padding: 10px;
  margin-bottom: 15px;
  border-radius: 4px;
}

.alert-success {
  background: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.alert-error {
  background: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}

.user-info {
  position: absolute;
  top: 20px;
  right: 20px;
  color: white;
}

.logout-btn {
  background: #e74c3c;
  color: white;
  border: none;
  padding: 5px 10px;
  border-radius: 4px;
  cursor: pointer;
  margin-left: 10px;
}
</style>