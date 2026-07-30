import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'

import App from './App'
import './features/model-editor/model-editor.css'
import './styles.css'

const rootElement = document.getElementById('root')

if (!rootElement) {
  throw new Error('Missing root element')
}

createRoot(rootElement).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
