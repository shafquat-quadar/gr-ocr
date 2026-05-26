import { cn } from '../../lib/utils'

export interface AlertProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'destructive' | 'warning' | 'success'
}

export function Alert({ className, variant = 'default', ...props }: AlertProps) {
  const variants = {
    default: 'bg-background border-border text-foreground',
    destructive: 'bg-destructive/5 border-destructive/30 text-destructive',
    warning: 'bg-amber-50 border-amber-200 text-amber-800',
    success: 'bg-emerald-50 border-emerald-200 text-emerald-800',
  }

  return (
    <div
      role="alert"
      className={cn('relative w-full rounded-lg border p-3 text-sm', variants[variant], className)}
      {...props}
    />
  )
}

export function AlertTitle({ className, ...props }: React.HTMLAttributes<HTMLHeadingElement>) {
  return <h5 className={cn('mb-1 font-medium leading-none tracking-tight', className)} {...props} />
}

export function AlertDescription({ className, ...props }: React.HTMLAttributes<HTMLParagraphElement>) {
  return <div className={cn('text-xs opacity-90', className)} {...props} />
}
