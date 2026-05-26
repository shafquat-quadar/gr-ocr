import { NavLink } from 'react-router-dom'
import { LayoutDashboard, Upload, AlertTriangle, CheckSquare, BarChart2, Package } from 'lucide-react'
import { cn } from '../../lib/utils'

const nav = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard', end: true },
  { to: '/upload', icon: Upload, label: 'Upload GR' },
  { to: '/exceptions', icon: AlertTriangle, label: 'Exceptions' },
  { to: '/posted', icon: CheckSquare, label: 'Posted GRs' },
  { to: '/reports', icon: BarChart2, label: 'Reports' },
]

export default function Sidebar() {
  return (
    <aside className="hidden lg:flex flex-col w-56 shrink-0 border-r bg-card h-screen sticky top-0">
      <div className="flex items-center gap-2 px-4 py-4 border-b">
        <Package className="h-5 w-5 text-primary" />
        <span className="font-semibold text-sm">GR Agent POC</span>
      </div>
      <nav className="flex-1 overflow-y-auto py-3 px-2 space-y-0.5">
        {nav.map(({ to, icon: Icon, label, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
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
      <div className="px-4 py-3 border-t text-xs text-muted-foreground">
        OCR · Mock SAP · Local POC
      </div>
    </aside>
  )
}
