import { Link, useLocation } from 'react-router-dom'
import { Group, Anchor } from '@mantine/core'

const linkStyle: React.CSSProperties = { textDecoration: 'none', padding: '8px 12px', borderRadius: 6 }
const activeStyle: React.CSSProperties = { background: 'rgba(255,255,255,0.06)' }

export function Nav() {
  const { pathname } = useLocation()
  const is = (p: string) => pathname === p
  return (
    <Group justify="space-between" p="md" style={{ borderBottom: '1px solid rgba(255,255,255,0.08)', background: 'transparent' }}>
      <div style={{ fontWeight: 600 }}>SMC Web</div>
      <Group gap="xs">
        <Anchor component={Link} to="/" style={{ ...linkStyle, ...(is('/') ? activeStyle : {}) }}>Dashboard</Anchor>
        <Anchor component={Link} to="/mtf" style={{ ...linkStyle, ...(is('/mtf') ? activeStyle : {}) }}>MTF</Anchor>
        <Anchor component={Link} to="/backtest" style={{ ...linkStyle, ...(is('/backtest') ? activeStyle : {}) }}>Backtesting</Anchor>
        <Anchor component={Link} to="/ml" style={{ ...linkStyle, ...(is('/ml') ? activeStyle : {}) }}>ML</Anchor>
      </Group>
    </Group>
  )
}


