import React from 'react'

export class ErrorBoundary extends React.Component<{ children: React.ReactNode }, { hasError: boolean; error?: any }>{
  constructor(props: any) {
    super(props)
    this.state = { hasError: false }
  }
  static getDerivedStateFromError(error: any) { return { hasError: true, error } }
  componentDidCatch(error: any, info: any) { console.error('UI Error', error, info) }
  render() {
    if (this.state.hasError) {
      return <div style={{ padding: 16 }}>
        <h3>Se produjo un error en la UI</h3>
        <pre style={{ background: '#111', color: '#ddd', padding: 8 }}>{String(this.state.error)}</pre>
      </div>
    }
    return this.props.children
  }
}


