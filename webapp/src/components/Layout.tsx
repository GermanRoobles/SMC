import { Nav } from './Nav'
import { AppShell } from '@mantine/core'

export function Layout({ sidebar, children }: { sidebar?: React.ReactNode; children: React.ReactNode }) {
  return (
    <AppShell
      header={{ height: 56 }}
      navbar={sidebar ? { width: 320, breakpoint: 'sm' } : undefined}
      padding="md"
      withBorder={false}
      styles={{
        main: {
          maxWidth: '100%',
          width: '100%',
          paddingLeft: sidebar ? 0 : undefined,
          paddingRight: 0,
        },
      }}
    >
      <AppShell.Header>
        <Nav />
      </AppShell.Header>
      {sidebar && (
        <AppShell.Navbar>
          <div style={{ padding: 8 }}>{sidebar}</div>
        </AppShell.Navbar>
      )}
      <AppShell.Main>
        {children}
      </AppShell.Main>
    </AppShell>
  )
}


