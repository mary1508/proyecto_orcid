// src/services/crud.js
import apiClient from './api'

export const createCrudService = (endpoint) => {
  return {
    async getAll() {
      try {
        const response = await apiClient.get(endpoint)
        return response.data
      } catch (error) {
        throw new Error(`Error obteniendo datos: ${error.response?.data?.message || error.message}`)
      }
    },

    async getById(id) {
      try {
        const response = await apiClient.get(`${endpoint}/${id}`)
        return response.data
      } catch (error) {
        throw new Error(`Error obteniendo registro: ${error.response?.data?.message || error.message}`)
      }
    },

    async create(data) {
      try {
        const response = await apiClient.post(endpoint, data)
        return response.data
      } catch (error) {
        throw new Error(`Error creando registro: ${error.response?.data?.message || error.message}`)
      }
    },

    async update(id, data) {
      try {
        const response = await apiClient.put(`${endpoint}/${id}`, data)
        return response.data
      } catch (error) {
        throw new Error(`Error actualizando registro: ${error.response?.data?.message || error.message}`)
      }
    },

    async delete(id) {
      try {
        const response = await apiClient.delete(`${endpoint}/${id}`)
        return response.data
      } catch (error) {
        throw new Error(`Error eliminando registro: ${error.response?.data?.message || error.message}`)
      }
    }
  }
}

// Servicios específicos para cada entidad
export const countriesService = createCrudService('/countries')
export const keywordsService = createCrudService('/keywords')
export const publicationTypesService = createCrudService('/publication-types')