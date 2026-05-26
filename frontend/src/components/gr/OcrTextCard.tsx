import { FileText } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card'
import { Skeleton } from '../ui/skeleton'

interface Props {
  ocrText?: string | null
  loading?: boolean
}

export function OcrTextCard({ ocrText, loading }: Props) {
  if (!loading && !ocrText) return null

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <FileText className="h-4 w-4 text-primary" />
          OCR Raw Text
        </CardTitle>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="space-y-2">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-3/4" />
            <Skeleton className="h-4 w-1/2" />
          </div>
        ) : (
          <pre className="whitespace-pre-wrap font-mono text-xs bg-muted/50 rounded-md p-3 max-h-48 overflow-auto border">
            {ocrText}
          </pre>
        )}
      </CardContent>
    </Card>
  )
}
