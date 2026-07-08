import { useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { setField } from '../store/interactionSlice'
import { addUserMessage, sendMessage } from '../store/chatSlice'
import { api } from '../api/client'
import useRecorder from '../hooks/useRecorder'
import ChipList from './ChipList'

const INTERACTION_TYPES = ['Meeting', 'Call', 'Email', 'Conference', 'Virtual', 'Other']
const SENTIMENTS = ['Positive', 'Neutral', 'Negative']

export default function InteractionForm() {
  const dispatch = useDispatch()
  const form = useSelector((s) => s.interaction.form)
  const flash = useSelector((s) => s.interaction.flash)
  const recorder = useRecorder()
  const [transcribing, setTranscribing] = useState(false)

  // Add "flash" class to a field wrapper when the AI just updated it.
  const cls = (key, base = 'field') =>
    `${base}${flash.includes(key) ? ' field--flash' : ''}`

  const update = (field, value) => dispatch(setField({ field, value }))

  // Send a transcript to the agent, scoped to summarize_notes only.
  const runSummarize = (raw) => {
    const display = `🎙 Voice note: "${raw.trim()}"`
    const instruction =
      'Use the summarize_notes tool to summarize this voice-note transcript into ' +
      'the Topics Discussed field. Do not change any other fields.\n\nTranscript:\n' +
      raw.trim()
    dispatch(addUserMessage(display))
    dispatch(sendMessage(instruction))
  }

  // Fallback: paste a transcript instead of recording.
  const pasteSummarize = () => {
    const raw = window.prompt(
      'Paste the raw voice-note transcript to summarize into Topics Discussed:',
      ''
    )
    if (raw && raw.trim()) runSummarize(raw)
  }

  // Record from the mic → transcribe via Groq Whisper → summarize.
  const toggleRecord = async () => {
    if (!recorder.supported) {
      alert('Recording is not supported in this browser. Use "Paste" instead.')
      return
    }
    if (!recorder.recording) {
      try {
        await recorder.start()
      } catch {
        alert('Microphone permission denied or unavailable.')
      }
      return
    }
    // Second click = stop, then transcribe.
    setTranscribing(true)
    try {
      const { base64, mime } = await recorder.stop()
      const { text } = await api.transcribe(base64, mime)
      if (text && !text.startsWith('⚠️')) {
        runSummarize(text)
      } else {
        alert(text || 'No speech was detected. Please try again.')
      }
    } catch (e) {
      alert('Transcription failed: ' + e.message)
    } finally {
      setTranscribing(false)
    }
  }

  return (
    <section className="card form">
      <h2 className="card__title">Interaction Details</h2>

      <div className="row">
        <div className={cls('hcp_name')}>
          <label>HCP Name</label>
          <input
            placeholder="Search or select HCP..."
            value={form.hcp_name}
            onChange={(e) => update('hcp_name', e.target.value)}
          />
        </div>
        <div className={cls('interaction_type')}>
          <label>Interaction Type</label>
          <select
            value={form.interaction_type}
            onChange={(e) => update('interaction_type', e.target.value)}
          >
            {INTERACTION_TYPES.map((t) => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="row">
        <div className={cls('date')}>
          <label>Date</label>
          <input
            type="date"
            value={form.date}
            onChange={(e) => update('date', e.target.value)}
          />
        </div>
        <div className={cls('time')}>
          <label>Time</label>
          <input
            type="time"
            value={form.time}
            onChange={(e) => update('time', e.target.value)}
          />
        </div>
      </div>

      <div className={cls('attendees')}>
        <label>Attendees</label>
        <ChipList
          field="attendees"
          items={form.attendees}
          placeholder="Enter names or search..."
        />
      </div>

      <div className={cls('topics_discussed')}>
        <label>Topics Discussed</label>
        <textarea
          rows={3}
          placeholder="Enter key discussion points..."
          value={form.topics_discussed}
          onChange={(e) => update('topics_discussed', e.target.value)}
        />
      </div>
      <div className="voicenote">
        <button
          className={`btn btn--ghost voicenote__rec${recorder.recording ? ' is-recording' : ''}`}
          onClick={toggleRecord}
          disabled={transcribing}
        >
          {transcribing
            ? '⏳ Transcribing…'
            : recorder.recording
            ? '⏹ Stop Recording'
            : '🎙 Summarize from Voice Note (Requires Consent)'}
        </button>
        <button
          className="btn btn--small"
          onClick={pasteSummarize}
          disabled={transcribing || recorder.recording}
          title="Paste a transcript instead of recording"
        >
          📝 Paste
        </button>
      </div>

      <div className={cls('materials_shared')}>
        <div className="field__header">
          <label>Materials Shared</label>
        </div>
        <ChipList field="materials_shared" items={form.materials_shared} emptyText="No materials added" addLabel="🔍 Search/Add" />
      </div>

      <div className={cls('samples_distributed')}>
        <div className="field__header">
          <label>Samples Distributed</label>
        </div>
        <ChipList field="samples_distributed" items={form.samples_distributed} emptyText="No samples added" addLabel="➕ Add Sample" />
      </div>

      <div className={cls('sentiment', 'field field--sentiment')}>
        <label>Observed/Inferred HCP Sentiment</label>
        <div className="radios">
          {SENTIMENTS.map((s) => (
            <label key={s} className="radio">
              <input
                type="radio"
                name="sentiment"
                checked={form.sentiment === s}
                onChange={() => update('sentiment', s)}
              />
              <span>{s}</span>
            </label>
          ))}
        </div>
      </div>

      <div className={cls('outcomes')}>
        <label>Outcomes</label>
        <textarea
          rows={2}
          placeholder="Key outcomes or agreements..."
          value={form.outcomes}
          onChange={(e) => update('outcomes', e.target.value)}
        />
      </div>

      <div className={cls('follow_up_actions')}>
        <label>Follow-up Actions</label>
        <textarea
          rows={2}
          placeholder="Enter next steps or tasks..."
          value={form.follow_up_actions}
          onChange={(e) => update('follow_up_actions', e.target.value)}
        />
      </div>

      {form.ai_suggested_followups?.length > 0 && (
        <div className={cls('ai_suggested_followups')}>
          <label>AI Suggested Follow-ups:</label>
          <ul className="suggestions">
            {form.ai_suggested_followups.map((s, i) => (
              <li key={i}>+ {s}</li>
            ))}
          </ul>
        </div>
      )}
    </section>
  )
}
