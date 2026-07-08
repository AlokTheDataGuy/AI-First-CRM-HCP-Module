import InteractionForm from './components/InteractionForm'
import ChatPanel from './components/ChatPanel'

export default function App() {
  return (
    <div className="app">
      <header className="app__header">
        <h1>Log HCP Interaction</h1>
      </header>
      <div className="app__grid">
        <InteractionForm />
        <ChatPanel />
      </div>
    </div>
  )
}
