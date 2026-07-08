import { createSlice } from '@reduxjs/toolkit'

// The canonical shape of the Log Interaction form. The AI assistant fills
// these fields via `applyUpdates`; the user does not type them manually.
const emptyForm = {
  hcp_name: '',
  interaction_type: 'Meeting',
  date: '',
  time: '',
  attendees: [],
  topics_discussed: '',
  materials_shared: [],
  samples_distributed: [],
  sentiment: 'Neutral',
  outcomes: '',
  follow_up_actions: '',
  ai_suggested_followups: [],
}

const interactionSlice = createSlice({
  name: 'interaction',
  initialState: {
    form: { ...emptyForm },
    // Field keys changed by the most recent AI update — used to flash-highlight.
    flash: [],
  },
  reducers: {
    // Manual edit of a single field (kept available, but the flow is AI-driven).
    setField: (state, action) => {
      const { field, value } = action.payload
      state.form[field] = value
    },
    // Apply a delta returned by the agent and mark those fields for highlight.
    applyUpdates: (state, action) => {
      const updates = action.payload || {}
      Object.entries(updates).forEach(([key, value]) => {
        state.form[key] = value
      })
      state.flash = Object.keys(updates)
    },
    setSuggestions: (state, action) => {
      state.form.ai_suggested_followups = action.payload || []
    },
    clearFlash: (state) => {
      state.flash = []
    },
    resetForm: (state) => {
      state.form = { ...emptyForm }
      state.flash = []
    },
  },
})

export const { setField, applyUpdates, setSuggestions, clearFlash, resetForm } =
  interactionSlice.actions
export default interactionSlice.reducer
