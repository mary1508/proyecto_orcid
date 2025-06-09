<template>
  <div>
    <div class="search-bar">
      <input 
        type="text" 
        v-model="searchTerm" 
        @input="handleSearch"
        placeholder="Buscar países..."
      >
      <button class="btn btn-success" @click="$emit('create')">
        Nuevo País
      </button>
    </div>
    
    <table class="table">
      <thead>
        <tr>
          <th>Nombre</th>
          <th>Código</th>
          <th>Acciones</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="item in items" :key="item.id">
          <td>{{ item.name }}</td>
          <td>{{ item.code }}</td>
          <td>
            <button class="btn" @click="$emit('edit', item)">
              Editar
            </button>
            <button class="btn btn-danger" @click="$emit('delete', item.id)">
              Eliminar
            </button>
          </td>
        </tr>
      </tbody>
    </table>
    
    <!-- Pagination -->
    <div class="pagination" v-if="totalPages > 1">
      <button 
        class="btn" 
        @click="$emit('page-change', currentPage - 1)" 
        :disabled="currentPage === 1"
      >
        Anterior
      </button>
      <span style="margin: 0 15px;">
        Página {{ currentPage }} de {{ totalPages }}
      </span>
      <button 
        class="btn" 
        @click="$emit('page-change', currentPage + 1)" 
        :disabled="currentPage === totalPages"
      >
        Siguiente
      </button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'CountriesTable',
  props: {
    items: {
      type: Array,
      default: () => []
    },
    loading: {
      type: Boolean,
      default: false
    },
    currentPage: {
      type: Number,
      default: 1
    },
    totalPages: {
      type: Number,
      default: 1
    }
  },
  data() {
    return {
      searchTerm: ''
    }
  },
  emits: ['create', 'edit', 'delete', 'search', 'page-change'],
  methods: {
    handleSearch() {
      this.$emit('search', this.searchTerm);
    }
  }
}
</script>

<style scoped>
.search-bar {
  margin-bottom: 20px;
}

.search-bar input {
  width: 300px;
  display: inline-block;
}

.table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 20px;
}

.table th,
.table td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid #ddd;
}

.table th {
  background: #f8f9fa;
  font-weight: bold;
}

.table tr:hover {
  background: #f5f5f5;
}

.pagination {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

.pagination button {
  margin: 0 5px;
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
</style>