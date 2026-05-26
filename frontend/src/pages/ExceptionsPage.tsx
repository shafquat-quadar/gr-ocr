import { useEffect, useState } from 'react'
import { NavLink } from 'react-router-dom'
import { AlertTriangle, RefreshCw, ArrowRight } from 'lucide-react'
import { getLocalDraftsByStatus } from '../lib/localDraftStore'
import { StatusBadge } from '../components/gr/StatusBadge'
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell, TableEmpty } from '../components/ui/table'
import { Button } from '../components/ui/button'
import { formatDate } from '../lib/utils'
import type { LocalDraftSummary } from '../types/gr'

export default function ExceptionsPage() {
  const [drafts, setDrafts] = useState<LocalDraftSummary[]>([])

  function refresh() {
    setDrafts(getLocalDraftsByStatus('NEEDS_CORRECTION', 'BLOCKED', 'FAILED'))
  }

  useEffect(() => { refresh() }, [])

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-amber-500" />
            Exceptions
          </h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            Drafts requiring attention — from this browser session
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={refresh}>
          <RefreshCw className="h-3.5 w-3.5" />
          Refresh
        </Button>
      </div>

      <div className="rounded-lg border bg-card overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Request ID</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>PO Number</TableHead>
              <TableHead>Last Updated</TableHead>
              <TableHead className="w-10" />
            </TableRow>
          </TableHeader>
          <TableBody>
            {drafts.length === 0 ? (
              <TableEmpty colSpan={5}>
                <div className="flex flex-col items-center gap-2">
                  <AlertTriangle className="h-6 w-6 text-muted-foreground/40" />
                  <span>No local exceptions yet.</span>
                  <span className="text-xs">Drafts with NEEDS_CORRECTION, BLOCKED or FAILED status will appear here.</span>
                </div>
              </TableEmpty>
            ) : (
              drafts.map((d) => (
                <TableRow key={d.request_id}>
                  <TableCell className="font-mono text-xs">{d.request_id}</TableCell>
                  <TableCell><StatusBadge status={d.status} /></TableCell>
                  <TableCell>{d.po_number ?? '—'}</TableCell>
                  <TableCell className="text-xs text-muted-foreground">{formatDate(d.updated_at ?? d.created_at)}</TableCell>
                  <TableCell>
                    <NavLink to={`/drafts/${d.request_id}`} className="text-muted-foreground hover:text-primary transition-colors">
                      <ArrowRight className="h-4 w-4" />
                    </NavLink>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  )
}
