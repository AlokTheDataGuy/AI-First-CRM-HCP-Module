import { useRef, useState } from 'react'

// Minimal microphone recorder built on MediaRecorder. `stop()` resolves with the
// recorded audio as a base64 data URL, ready to POST to the transcribe endpoint.
export default function useRecorder() {
  const [recording, setRecording] = useState(false)
  const recorderRef = useRef(null)
  const chunksRef = useRef([])
  const streamRef = useRef(null)
  const resolveRef = useRef(null)
 
  const supported =
    typeof window !== 'undefined' &&
    !!navigator.mediaDevices?.getUserMedia &&
    typeof MediaRecorder !== 'undefined'

  const start = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    streamRef.current = stream
    chunksRef.current = []

    const mime = MediaRecorder.isTypeSupported('audio/webm')
      ? 'audio/webm'
      : MediaRecorder.isTypeSupported('audio/ogg')
      ? 'audio/ogg'
      : ''
    const mr = mime
      ? new MediaRecorder(stream, { mimeType: mime })
      : new MediaRecorder(stream)
    recorderRef.current = mr

    mr.ondataavailable = (e) => {
      if (e.data && e.data.size > 0) chunksRef.current.push(e.data)
    }
    mr.onstop = () => {
      const blob = new Blob(chunksRef.current, { type: mr.mimeType || 'audio/webm' })
      streamRef.current?.getTracks().forEach((t) => t.stop())
      const reader = new FileReader()
      reader.onloadend = () =>
        resolveRef.current?.({ base64: reader.result, mime: blob.type })
      reader.readAsDataURL(blob)
    }

    mr.start()
    setRecording(true)
  }

  const stop = () =>
    new Promise((resolve) => {
      resolveRef.current = resolve
      setRecording(false)
      recorderRef.current?.stop()
    })

  return { recording, supported, start, stop }
}
