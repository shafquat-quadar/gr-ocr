import { useEffect, useState } from 'react'
import { BarChart2, RefreshCw, CheckCircle2, AlertTriangle, Activity, Edit3 } from 'lucide-react'
import { getLocalDrafts } from '../lib/localDraftStore'
import { KpiCard } from '../components/reports/KpiCard'
import { StatusDistributionChart } from '../components/reports/StatusDistributionChart'
import { DailyVolumeChart } from '../components/reports/DailyVolumeChart'
import { ValidationErrorChart } from '../components/reports/ValidationErrorChart'
import { Alert, AlertDescription } from '../components/ui/alert'
import { Button } from '../components/ui/button'
import { Separator } from '../components/ui/separator'
import type { LocalDraftSummary } from '../types/gr'

export default function ReportsPage() {
  const [drafts, setDrafts] = useState<LocalDraftSummary[]>([])

  function refresh() { setDrafts(getLocalDrafts()) }
  useEffect(() => { refresh() }, [])

  const posted = drafts.filter((d) => d.status === 'POSTED').length
  const exceptions = drafts.filter((d) => ['NEEDS_CORRECTION', 'BLOCKED', 'FAILED'].includes(d.status)).length
  const ready = drafts.filter((d) => d.status === 'READY_FOR_CONFIRMATION').length
  const needsCorrection = drafts.filter((d) => d.status === 'NEEDS_CORRECTION').length

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold flex items-center gap-2">
            <BarChart2 className="h-5 w-5 text-primary" />
            Reports
          </h1>
          <p className="text-sm text-muted-foreground mt-0.5">Local session reporting</p>
        </div>
        <Button variant="outline" size="sm" onClick={refresh}>
          <RefreshCw className="h-3.5 w-3.5" />
          Refresh
        </Button>
      </div>

      <Alert>
        <AlertDescription>
          Reports are based on drafts created from <strong>this browser/session</strong> because the backend does not expose global report or list endpoints. Data resets if localStorage is cleared.
        </AlertDescription>
      </Alert>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <KpiCard title="Posted" value={posted} icon={<CheckCircle2 className="h-5 w-5" />} variant="success" />
        <KpiCard title="Exceptions" value={exceptions} icon={<AlertTriangle className="h-5 w-5" />} variant="warning" />
        <KpiCard title="Ready to Confirm" value={ready} icon={<Activity className="h-5 w-5" />} />
        <KpiCard title="Manual Corrections" value={needsCorrection} icon={<Edit3 className="h-5 w-5" />} variant="warning" description="NEEDS_CORRECTION status" />
      </div>

      <Separator />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <StatusDistributionChart drafts={drafts} />
        <DailyVolumeChart drafts={drafts} />
      </div>

      <ValidationErrorChart drafts={drafts} />
    </div>
  )
}
