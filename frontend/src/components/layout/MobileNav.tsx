import { useState } from 'react'
import { NavLink } from 'react-router-dom'
import { Menu, X, LayoutDashboard, Upload, AlertTriangle, CheckSquare, BarChart2 } from 'lucide-react'
import { cn } from '../../lib/utils'

const nav = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard', end: true },
  { to: '/upload', icon: Upload, label: 'Upload GR' },
  { to: '/exceptions', icon: AlertTriangle, label: 'Exceptions' },
  { to: '/posted', icon: CheckSquare, label: 'Posted GRs' },
  { to: '/reports', icon: BarChart2, label: 'Reports' },
]

export default function MobileNav() {
  const [open, setOpen] = useState(false)

  return (
    <>
      <button onClick={() => setOpen(true)} className="p-1 rounded-md hover:bg-accent">
        <Menu className="h-5 w-5" />
      </button>

      {open && (
        <div className="fixed inset-0 z-50 flex">
          <div className="fixed inset-0 bg-black/40" onClick={() => setOpen(false)} />
          <aside className="relative z-50 flex w-64 flex-col bg-card border-r shadow-xl">
            <div className="flex items-center justify-between px-4 py-4 border-b">
              <span className="font-semibold text-sm">GR Agent POC</span>
              <button onClick={() => setOpen(false)} className="p-1 rounded-md hover:bg-accent">
                <X className="h-4 w-4" />
              </button>
            </div>
            <nav className="flex-1 py-3 px-2 space-y-0.5">
              {nav.map(({ to, icon: Icon, label, end }) => (
                <NavLink
                  key={to}
                  to={to}
                  end={end}
                  onClick={() => setOpen(false)}
                  className={({ isActive }) =>
                    cn(
                      'flex items-center gap-2.5 rounded-md px-3 py-2 text-sm font-medium transition-colors',
                      isActive
                        ? 'bg-primary/10 text-primary'
                        : 'text-muted-foreground hover:bg-accent hover:text-foreground',
                    )
                  }
                >
                  <Icon className="h-4 w-4 shrink-0" />
                  {label}
                </NavLink>
              ))}
            </nav>
          </aside>
        </div>
      )}
    </>
  )
}
