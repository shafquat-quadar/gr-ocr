import { useEffect, useState } from 'react'
import { NavLink } from 'react-router-dom'
import { Upload, Activity, Server, CheckCircle2, AlertTriangle, XCircle, Package, RefreshCw } from 'lucide-react'
import { useHealth } from '../hooks/useHealth'
import { useSapPing } from '../hooks/useSapPing'
import { getLocalDrafts } from '../lib/localDraftStore'
import { KpiCard } from '../components/reports/KpiCard'
import { DraftSummaryCard } from '../components/gr/DraftSummaryCard'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card'
import { Badge } from '../components/ui/badge'
import { Button } from '../components/ui/button'
import { Skeleton } from '../components/ui/skeleton'
import type { LocalDraftSummary } from '../types/gr'

export default function DashboardPage() {
  const health = useHealth()
  const sap = useSapPing()
  const [drafts, setDrafts] = useState<LocalDraftSummary[]>([])

  function refresh() { setDrafts(getLocalDrafts()) }
  useEffect(() => { refresh() }, [])

  const total = drafts.length
  const posted = drafts.filter((d) => d.status === 'POSTED').length
  const ready = drafts.filter((d) => d.status === 'READY_FOR_CONFIRMATION').length
  const needsCorrection = drafts.filter((d) => d.status === 'NEEDS_CORRECTION').length
  const blocked = drafts.filter((d) => d.status === 'BLOCKED' || d.status === 'FAILED').length

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold">Dashboard</h1>
          <p className="text-sm text-muted-foreground mt-0.5">GR Agent POC — OCR-Based SAP Goods Receipt</p>
        </div>
        <NavLink to="/upload">
          <Button size="sm">
            <Upload className="h-3.5 w-3.5" />
            Upload Package Image
          </Button>
        </NavLink>
      </div>

      {/* Connectivity */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <ConnectivityCard
          title="Backend API"
          icon={<Server className="h-4 w-4" />}
          status={health.data?.status}
          loading={health.isLoading}
          error={health.isError}
          detail={`http://localhost:8000`}
        />
        <ConnectivityCard
          title="SAP Connectivity"
          icon={<Activity className="h-4 w-4" />}
          status={sap.data?.status}
          loading={sap.isLoading}
          error={sap.isError}
          detail={sap.data ? `Mode: ${sap.data.sap_mode?.toUpperCase() ?? '—'}` : undefined}
        />
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
        <KpiCard title="Total (local)" value={total} icon={<Package className="h-5 w-5" />} />
        <KpiCard title="Posted" value={posted} icon={<CheckCircle2 className="h-5 w-5" />} variant="success" />
        <KpiCard title="Ready to Confirm" value={ready} icon={<Activity className="h-5 w-5" />} variant="default" />
        <KpiCard title="Needs Correction" value={needsCorrection} icon={<AlertTriangle className="h-5 w-5" />} variant="warning" />
        <KpiCard title="Blocked / Failed" value={blocked} icon={<XCircle className="h-5 w-5" />} variant="destructive" />
      </div>

      {/* Recent local drafts */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-semibold">
            Recent Local Drafts
            <span className="ml-2 text-xs font-normal text-muted-foreground">(from this browser)</span>
          </h2>
          <Button variant="ghost" size="sm" onClick={refresh}>
            <RefreshCw className="h-3.5 w-3.5" />
            Refresh
          </Button>
        </div>

        {drafts.length === 0 ? (
          <EmptyState />
        ) : (
          <div className="space-y-2">
            {drafts.slice(0, 10).map((d) => (
              <DraftSummaryCard key={d.request_id} draft={d} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function ConnectivityCard({
  title, icon, status, loading, error, detail,
}: {
  title: string
  icon: React.ReactNode
  status?: string
  loading?: boolean
  error?: boolean
  detail?: string
}) {
  const ok = !error && status && status !== 'error'
  return (
    <Card>
      <CardHeader className="pb-1">
        <CardTitle className="flex items-center gap-2 text-xs text-muted-foreground font-medium uppercase tracking-wide">
          {icon}
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent className="flex items-center justify-between">
        {loading ? (
          <Skeleton className="h-5 w-24" />
        ) : (
          <>
            <span className="text-sm">{detail ?? '—'}</span>
            <Badge variant={error ? 'destructive' : ok ? 'success' : 'secondary'}>
              {error ? 'Unreachable' : ok ? 'OK' : status ?? 'Unknown'}
            </Badge>
          </>
        )}
      </CardContent>
    </Card>
  )
}

function EmptyState() {
  return (
    <div className="rounded-lg border border-dashed border-border py-12 text-center">
      <Package className="h-8 w-8 text-muted-foreground mx-auto mb-3" />
      <p className="text-sm font-medium">No local drafts yet</p>
      <p className="text-xs text-muted-foreground mt-1 mb-4">
        Drafts created from this browser will appear here.
      </p>
      <NavLink to="/upload">
        <Button size="sm">
          <Upload className="h-3.5 w-3.5" />
          Upload your first image
        </Button>
      </NavLink>
    </div>
  )
}
