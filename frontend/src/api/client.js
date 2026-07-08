// Thin fetch wrapper around the backend API.
const BASE = import.meta.env.VITE_API_BASE || ''

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new Error(`API ${res.status}: ${text || res.statusText}`)
  }
  return res.json()
}

export const api = {
  // Send a chat message to the LangGraph agent.
  chat: (payload) =>
    request('/api/chat', { method: 'POST', body: JSON.stringify(payload) }),

  // Persist the current form (the "Log" button).
  saveInteraction: (payload) =>
    request('/api/interactions', { method: 'POST', body: JSON.stringify(payload) }),

  // HCP autocomplete.
  listHcps: (q = '') => request(`/api/hcps${q ? `?q=${encodeURIComponent(q)}` : ''}`),

  // Transcribe a recorded voice note via Groq Whisper.
  transcribe: (audio_base64, mime) =>
    request('/api/transcribe', {
      method: 'POST',
      body: JSON.stringify({ audio_base64, mime }),
    }),
}
