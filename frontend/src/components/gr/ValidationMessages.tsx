import { AlertTriangle, XCircle, Info } from 'lucide-react'
import type { ValidationMessage } from '../../types/gr'
import { cn } from '../../lib/utils'

export function ValidationMessages({ messages }: { messages: ValidationMessage[] }) {
  if (!messages || messages.length === 0) return null

  const errors = messages.filter((m) => m.severity === 'error')
  const warnings = messages.filter((m) => m.severity === 'warning')
  const infos = messages.filter((m) => m.severity === 'info')

  return (
    <div className="space-y-2">
      {errors.map((m, i) => (
        <MessageRow key={i} message={m} />
      ))}
      {warnings.map((m, i) => (
        <MessageRow key={i} message={m} />
      ))}
      {infos.map((m, i) => (
        <MessageRow key={i} message={m} />
      ))}
    </div>
  )
}

function MessageRow({ message: m }: { message: ValidationMessage }) {
  const isError = m.severity === 'error'
  const isWarning = m.severity === 'warning'

  return (
    <div
      className={cn(
        'flex items-start gap-2 rounded-md border px-3 py-2 text-sm',
        isError && 'bg-destructive/5 border-destructive/25 text-destructive',
        isWarning && 'bg-amber-50 border-amber-200 text-amber-800',
        !isError && !isWarning && 'bg-blue-50 border-blue-200 text-blue-800',
      )}
    >
      {isError ? (
        <XCircle className="h-4 w-4 mt-0.5 shrink-0" />
      ) : isWarning ? (
        <AlertTriangle className="h-4 w-4 mt-0.5 shrink-0" />
      ) : (
        <Info className="h-4 w-4 mt-0.5 shrink-0" />
      )}
      <div className="flex-1 min-w-0">
        <span className="font-mono text-xs font-medium">[{m.code}]</span>{' '}
        <span>{m.message}</span>
      </div>
    </div>
  )
}
