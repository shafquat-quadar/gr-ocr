import { useEffect, useState } from 'react'
import { Eye } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card'

export function ImagePreviewCard({ file }: { file: File | null }) {
  const [src, setSrc] = useState<string | null>(null)

  useEffect(() => {
    if (!file) { setSrc(null); return }
    const url = URL.createObjectURL(file)
    setSrc(url)
    return () => URL.revokeObjectURL(url)
  }, [file])

  if (!src) return null

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Eye className="h-4 w-4 text-primary" />
          Image Preview
        </CardTitle>
      </CardHeader>
      <CardContent>
        <img
          src={src}
          alt="Package label preview"
          className="w-full max-h-64 object-contain rounded-md border bg-muted"
        />
      </CardContent>
    </Card>
  )
}
