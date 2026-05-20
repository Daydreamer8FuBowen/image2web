function resolveApiBaseUrl() {
  const configured = import.meta.env.VITE_API_BASE_URL?.trim()
  if (configured) {
    return configured
  }

  if (typeof window !== 'undefined') {
    return window.location.origin
  }

  return ''
}

export const env = {
  apiBaseUrl: resolveApiBaseUrl(),
}
