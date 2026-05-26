import axios from 'axios'

const BASE_URL = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? 'http://localhost:8000'

export const apiClient = axios.create({
  baseURL: BASE_URL,
  timeout: 30_000,
})

apiClient.interceptors.response.use(
  (res) => res,
  (error) => {
    if (axios.isAxiosError(error)) {
      const status = error.response?.status
      const data = error.response?.data as { detail?: string | { msg: string }[] } | undefined

      let message = 'An unexpected error occurred.'

      if (!error.response) {
        message = 'Cannot reach backend. Is the server running at ' + BASE_URL + '?'
      } else if (status === 404) {
        message = 'Resource not found.'
      } else if (status === 422) {
        const detail = data?.detail
        if (Array.isArray(detail)) {
          message = detail.map((d) => d.msg).join('; ')
        } else if (typeof detail === 'string') {
          message = detail
        } else {
          message = 'Validation error.'
        }
      } else if (status === 500) {
        message = 'Internal server error. Check backend logs.'
      } else if (typeof data?.detail === 'string') {
        message = data.detail
      }

      return Promise.reject(new Error(message))
    }
    return Promise.reject(error)
  },
)
