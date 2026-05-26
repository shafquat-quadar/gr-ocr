import { useRef, useState } from 'react'
import { Upload, FileImage, X } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card'
import { Button } from '../ui/button'
import { cn } from '../../lib/utils'

interface Props {
  onFileSelected: (file: File) => void
  selectedFile: File | null
  onClear: () => void
}

const ALLOWED = ['image/jpeg', 'image/png']
const MAX_MB = 10

export function ImageUploadCard({ onFileSelected, selectedFile, onClear }: Props) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [dragOver, setDragOver] = useState(false)
  const [error, setError] = useState<string | null>(null)

  function validate(file: File): string | null {
    if (!ALLOWED.includes(file.type)) return 'Only JPEG and PNG images are allowed.'
    if (file.size > MAX_MB * 1024 * 1024) return `File must be under ${MAX_MB} MB.`
    return null
  }

  function handleFile(file: File) {
    const err = validate(file)
    if (err) { setError(err); return }
    setError(null)
    onFileSelected(file)
  }

  function onDrop(e: React.DragEvent) {
    e.preventDefault()
    setDragOver(false)
    const file = e.dataTransfer.files[0]
    if (file) handleFile(file)
  }

  function onChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (file) handleFile(file)
    e.target.value = ''
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <FileImage className="h-4 w-4 text-primary" />
          Package Label Image
        </CardTitle>
      </CardHeader>
      <CardContent>
        {selectedFile ? (
          <div className="flex items-center gap-3 rounded-md border border-dashed border-primary/40 bg-primary/5 px-4 py-3">
            <FileImage className="h-8 w-8 text-primary shrink-0" />
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate">{selectedFile.name}</p>
              <p className="text-xs text-muted-foreground">
                {(selectedFile.size / 1024).toFixed(0)} KB · {selectedFile.type}
              </p>
            </div>
            <Button variant="ghost" size="icon" onClick={onClear} className="shrink-0">
              <X className="h-4 w-4" />
            </Button>
          </div>
        ) : (
          <div
            onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
            onDragLeave={() => setDragOver(false)}
            onDrop={onDrop}
            onClick={() => inputRef.current?.click()}
            className={cn(
              'flex flex-col items-center gap-3 rounded-md border-2 border-dashed p-8 cursor-pointer transition-colors',
              dragOver ? 'border-primary bg-primary/5' : 'border-border hover:border-primary/50 hover:bg-accent/50',
            )}
          >
            <Upload className="h-8 w-8 text-muted-foreground" />
            <div className="text-center">
              <p className="text-sm font-medium">Drop image here or click to browse</p>
              <p className="text-xs text-muted-foreground mt-1">JPEG or PNG, max {MAX_MB} MB</p>
            </div>
          </div>
        )}

        {error && (
          <p className="mt-2 text-xs text-destructive">{error}</p>
        )}

        <input
          ref={inputRef}
          type="file"
          accept="image/jpeg,image/png"
          className="hidden"
          onChange={onChange}
        />
      </CardContent>
    </Card>
  )
}
