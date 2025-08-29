/**
 * API configuration and utilities for the frontend
 */

// API base URL - defaults to localhost:8080, can be overridden with environment variable
export const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8080'

// API endpoints
export const API_ENDPOINTS = {
  jobs: '/api/v1/jobs',
  symbols: '/api/v1/symbols',
  health: '/health'
} as const

/**
 * Make an API request with proper error handling
 */
export async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE}${endpoint}`
  
  try {
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    })

    if (!response.ok) {
      throw new Error(`API request failed: ${response.status} ${response.statusText}`)
    }

    return await response.json()
  } catch (error) {
    console.error('API request error:', error)
    throw error
  }
}

/**
 * Get jobs list
 */
export async function getJobs() {
  return apiRequest<{
    jobs: any[]
    total: number
    page: number
    size: number
    has_next: boolean
  }>(API_ENDPOINTS.jobs)
}

/**
 * Create a new job
 */
export async function createJob(jobData: any) {
  return apiRequest<{
    job_id: string
    status: string
    message: string
    estimated_duration: number
  }>(API_ENDPOINTS.jobs, {
    method: 'POST',
    body: JSON.stringify(jobData),
  })
}

/**
 * Get job details by ID
 */
export async function getJob(id: string) {
  return apiRequest<any>(`${API_ENDPOINTS.jobs}/${id}`)
}

/**
 * Cancel a job
 */
export async function cancelJob(id: string) {
  return apiRequest<{ message: string }>(`${API_ENDPOINTS.jobs}/${id}`, {
    method: 'DELETE',
  })
}

/**
 * Get available symbols
 */
export async function getSymbols() {
  return apiRequest<{
    symbols: string[]
    total: number
  }>(API_ENDPOINTS.symbols)
}

/**
 * Health check
 */
export async function healthCheck() {
  return apiRequest<{
    status: string
    timestamp: string
    version: string
    database: string
    pubsub: string
  }>(API_ENDPOINTS.health)
}
