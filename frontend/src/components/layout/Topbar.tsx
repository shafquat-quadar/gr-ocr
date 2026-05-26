import { Package } from 'lucide-react'
import MobileNav from './MobileNav'

export default function Topbar() {
  return (
    <header className="lg:hidden sticky top-0 z-40 flex h-12 items-center gap-3 border-b bg-card px-4">
      <MobileNav />
      <div className="flex items-center gap-2">
        <Package className="h-4 w-4 text-primary" />
        <span className="font-semibold text-sm">GR Agent POC</span>
      </div>
    </header>
  )
}
