import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { createBrowserRouter, RouterProvider } from 'react-router-dom'
import { MantineProvider } from '@mantine/core'
import { ErrorBoundary } from './components/ErrorBoundary'
import './index.css'
import App from './App.tsx'
import MTFPage from './pages/MTF.tsx'
import BacktestPage from './pages/Backtest.tsx'
import MLPage from './pages/ML.tsx'

const router = createBrowserRouter([
  { path: '/', element: <App /> },
  { path: '/mtf', element: <MTFPage /> },
  { path: '/backtest', element: <BacktestPage /> },
  { path: '/ml', element: <MLPage /> },
])

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <MantineProvider forceColorScheme="dark" defaultColorScheme="dark" theme={{ fontFamily: 'Inter, system-ui, Arial' }}>
      <ErrorBoundary>
        <RouterProvider router={router} />
      </ErrorBoundary>
    </MantineProvider>
  </StrictMode>,
)
