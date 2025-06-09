import axios from 'axios'

class ApiService {
  constructor() {
    this.baseURL = 'http://127.0.0.1:5000/api/'
    this.token = localStorage.getItem('token')
    
    // Configure axios defaults
    axios.defaults.baseURL = this.baseURL
    
    if (this.token) {
      this.setAuthToken(this.token)
    }
    
    axios.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          this.logout()
        }
        return Promise.reject(error)
      }
    )
  }

  setAuthToken(token) {
    this.token = token
    axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
    localStorage.setItem('token', token)
  }

  removeAuthToken() {
    this.token = null
    delete axios.defaults.headers.common['Authorization']
    localStorage.removeItem('token')
  }

  logout() {
    this.removeAuthToken()
    localStorage.removeItem('user')
    window.location.reload()
  }

  // Authentication
  async login(credentials) {
    try {
      const response = await axios.post('/auth/login', credentials)
      const { access_token, user } = response.data
      
      this.setAuthToken(access_token)
      localStorage.setItem('user', JSON.stringify(user))
      
      return { token: access_token, user }
    } catch (error) {
      throw new Error(error.response?.data?.error || 'Error al iniciar sesión')
    }
  }

  // Generic CRUD operations
  async getItems(endpoint, params = {}) {
    try {
      const response = await axios.get(`/${endpoint}`, { params })
      return response.data
    } catch (error) {
      throw new Error(error.response?.data?.error || 'Error al cargar datos')
    }
  }

  async createItem(endpoint, data) {
    try {
      const response = await axios.post(`${endpoint}`, data)
      return response.data
    } catch (error) {
      throw new Error(error.response?.data?.error || 'Error al crear elemento')
    }
  }

  async updateItem(endpoint, id, data) {
  try {
    const formCopy = { ...data }
    delete formCopy.id  // Quitar ID del cuerpo, ya va en la URL

    const response = await axios.put(`${endpoint}/${id}`, formCopy)
    return response.data

  } catch (error) {
    console.error('Error del backend:', error.response?.data)
    throw new Error(error.response?.data?.error || 'Error al actualizar elemento')
  }
}


  async deleteItem(endpoint, id) {
    try {
      const response = await axios.delete(`/${endpoint}/${id}`)
      return response.data
    } catch (error) {
      throw new Error(error.response?.data?.error || 'Error al eliminar elemento')
    }
  }

  // Specific methods for each entity
  async getCountries(params = {}) {
    return this.getItems('countries', params)
  }

  async createCountry(data) {
    return this.createItem('countries', data)
  }

  async updateCountry(id, data) {
    return this.updateItem('countries', id, data)
  }

  async deleteCountry(id) {
    return this.deleteItem('countries', id)
  }

  async getKeywords(params = {}) {
    return this.getItems('keywords', params)
  }

  async createKeyword(data) {
    return this.createItem('keywords', data)
  }

  async updateKeyword(id, data) {
    return this.updateItem('keywords', id, data)
  }

  async deleteKeyword(id) {
    return this.deleteItem('keywords', id)
  }

  async getPublicationTypes(params = {}) {
    return this.getItems('publication-types', params)
  }

  async createPublicationType(data) {
    return this.createItem('publication-types', data)
  }

  async updatePublicationType(id, data) {
    return this.updateItem('publication-types', id, data)
  }

  async deletePublicationType(id) {
    return this.deleteItem('publication-types', id)
  }
}

export default new ApiService()