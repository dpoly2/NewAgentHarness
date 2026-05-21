import React from 'react'

export default function App(){
  return (
    <div className="app">
      <aside className="sidebar">
        <h2>Agents</h2>
        <ul>
          <li>wordpresspluginsagent — idle</li>
          <li>researchagent — running</li>
        </ul>
      </aside>
      <main className="main">
        <header className="timeline">Human-speed progress timeline (mock)</header>
        <section className="chat">Chat / Agent controls (prototype)</section>
        <section className="logs">Logs & status</section>
      </main>
    </div>
  )
}
