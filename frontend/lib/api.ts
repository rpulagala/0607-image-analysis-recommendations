const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

function getToken(): string | null {
  if (typeof window === 'undefined') return null
  return localStorage.getItem('access_token')
}

async function request(path: string, options: RequestInit = {}) {
  const token = getToken()
  const headers: Record<string, string> = {}

  if (options.body && !(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json'
  }
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: { ...headers, ...(options.headers as Record<string, string>) },
  })

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Request failed' }))
    const error = new Error(err.detail || 'Request failed') as Error & { status: number }
    error.status = res.status
    throw error
  }

  return res.json()
}

export const api = {
  get: (path: string) => request(path),

  post: (path: string, body?: object) =>
    request(path, { method: 'POST', body: body ? JSON.stringify(body) : undefined }),

  patch: (path: string, body?: object) =>
    request(path, { method: 'PATCH', body: body ? JSON.stringify(body) : undefined }),

  upload: (path: string, file: File) => {
    const form = new FormData()
    form.append('file', file)
    return request(path, { method: 'POST', body: form })
  },
}
