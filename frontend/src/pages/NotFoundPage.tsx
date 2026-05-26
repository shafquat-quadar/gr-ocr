import { NavLink } from 'react-router-dom'
import { ArrowLeft, FileQuestion } from 'lucide-react'
import { Button } from '../components/ui/button'

export default function NotFoundPage() {
  return (
    <div className="flex flex-col items-center justify-center py-24 text-center">
      <FileQuestion className="h-12 w-12 text-muted-foreground mb-4" />
      <h1 className="text-2xl font-bold">404 — Page Not Found</h1>
      <p className="text-sm text-muted-foreground mt-2 mb-6">
        The page you're looking for doesn't exist.
      </p>
      <NavLink to="/">
        <Button variant="outline">
          <ArrowLeft className="h-4 w-4" />
          Back to Dashboard
        </Button>
      </NavLink>
    </div>
  )
}
