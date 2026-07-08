import { createAsyncThunk, createSlice } from '@reduxjs/toolkit'
import { api } from '../api/client'
import { applyUpdates, clearFlash } from './interactionSlice'

// Send a message to the LangGraph agent, then push the returned form delta
// into the interaction slice (so the left panel updates itself).
export const sendMessage = createAsyncThunk(
  'chat/sendMessage',
  async (text, { getState, dispatch }) => {
    const state = getState()
    const form = state.interaction.form
    // Prior turns only. The current message was already pushed to the UI by
    // addUserMessage, so drop the trailing duplicate — the backend appends it.
    const msgs = state.chat.messages
    const prior = msgs.slice(
      0,
      msgs.length && msgs[msgs.length - 1].content === text ? -1 : undefined
    )
    // Cap history to the last 6 messages to keep token usage bounded — the
    // current form snapshot (sent separately) carries the important state.
    const history = prior.slice(-6).map((m) => ({ role: m.role, content: m.content }))

    const data = await api.chat({ message: text, form, history })

    if (data.form_updates && Object.keys(data.form_updates).length) {
      dispatch(applyUpdates(data.form_updates))
      // Remove the highlight after a short flash.
      setTimeout(() => dispatch(clearFlash()), 1600)
    }
    return data // { reply, form_updates, suggestions, tool_calls }
  }
)

const chatSlice = createSlice({
  name: 'chat',
  initialState: {
    messages: [
      {
        role: 'assistant',
        content:
          'Log interaction details here (e.g., "Met Dr. Smith, discussed Product X ' +
          'efficacy, positive sentiment, shared brochure") or ask for help.',
        tools: [],
      },
    ],
    status: 'idle', // idle | loading
    error: null,
  },
  reducers: {
    addUserMessage: (state, action) => {
      state.messages.push({ role: 'user', content: action.payload })
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(sendMessage.pending, (state) => {
        state.status = 'loading'
        state.error = null
      })
      .addCase(sendMessage.fulfilled, (state, action) => {
        state.status = 'idle'
        state.messages.push({
          role: 'assistant',
          content: action.payload.reply,
          tools: action.payload.tool_calls || [],
        })
      })
      .addCase(sendMessage.rejected, (state, action) => {
        state.status = 'idle'
        state.error = action.error.message
        state.messages.push({
          role: 'assistant',
          content: `⚠️ ${action.error.message}`,
          tools: [],
        })
      })
  },
})

export const { addUserMessage } = chatSlice.actions
export default chatSlice.reducer
