interface LoadingSpinnerProps {
  label?: string
  skeletonCards?: number
}

export default function LoadingSpinner({ label = 'Loading...', skeletonCards = 0 }: LoadingSpinnerProps) {
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3 text-slate-300">
        <span className="h-5 w-5 animate-spin rounded-full border-2 border-slate-600 border-t-blue-400" />
        <span>{label}</span>
      </div>
      {skeletonCards > 0 && (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {Array.from({ length: skeletonCards }).map((_, index) => (
            <div key={index} className="h-36 animate-pulse rounded-2xl border border-slate-800 bg-slate-900/70" />
          ))}
        </div>
      )}
    </div>
  )
}
