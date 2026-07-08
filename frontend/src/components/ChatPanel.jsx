import { useEffect, useRef, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { addUserMessage, sendMessage } from '../store/chatSlice'

export default function ChatPanel() {
  const dispatch = useDispatch()
  const messages = useSelector((s) => s.chat.messages)
  const status = useSelector((s) => s.chat.status)
  const [text, setText] = useState('')
  const scrollRef = useRef(null)

  useEffect(() => {
    scrollRef.current?.scrollTo(0, scrollRef.current.scrollHeight)
  }, [messages, status])

  const send = () => {
    const msg = text.trim()
    if (!msg || status === 'loading') return
    dispatch(addUserMessage(msg))
    dispatch(sendMessage(msg))
    setText('')
  }

  const onKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      send()
    }
  }

  return (
    <section className="card chat">
      <div className="chat__head">
        <span className="chat__badge">🤖 AI Assistant</span>
        <span className="chat__sub">Log interaction via chat</span>
      </div>

      <div className="chat__messages" ref={scrollRef}>
        {messages.map((m, i) => (
          <div key={i} className={`msg msg--${m.role}`}>
            <div className="msg__bubble">{m.content}</div>
            {m.tools?.length > 0 && (
              <div className="msg__tools">
                {m.tools.map((t, j) => (
                  <span key={j} className="tool-badge">🔧 {t}</span>
                ))}
              </div>
            )}
          </div>
        ))}
        {status === 'loading' && (
          <div className="msg msg--assistant">
            <div className="msg__bubble msg__bubble--typing">
              <span></span><span></span><span></span>
            </div>
          </div>
        )}
      </div>

      <div className="chat__input">
        <textarea
          rows={1}
          placeholder="Describe interaction..."
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={onKeyDown}
        />
        <button className="btn btn--primary" onClick={send} disabled={status === 'loading'}>
          {status === 'loading' ? '…' : '⚡ Log'}
        </button>
      </div>
    </section>
  )
}
