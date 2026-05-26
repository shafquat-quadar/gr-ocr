import { Card, CardContent } from '../ui/card'
import { cn } from '../../lib/utils'

interface Props {
  title: string
  value: number | string
  icon: React.ReactNode
  variant?: 'default' | 'success' | 'warning' | 'destructive'
  description?: string
}

export function KpiCard({ title, value, icon, variant = 'default', description }: Props) {
  const colors = {
    default: 'text-primary bg-primary/10',
    success: 'text-emerald-600 bg-emerald-50',
    warning: 'text-amber-600 bg-amber-50',
    destructive: 'text-destructive bg-destructive/10',
  }

  return (
    <Card>
      <CardContent className="flex items-center gap-4 py-4">
        <div className={cn('rounded-lg p-2.5 shrink-0', colors[variant])}>
          {icon}
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-xs text-muted-foreground font-medium">{title}</p>
          <p className="text-2xl font-bold tabular-nums">{value}</p>
          {description && <p className="text-xs text-muted-foreground mt-0.5">{description}</p>}
        </div>
      </CardContent>
    </Card>
  )
}
