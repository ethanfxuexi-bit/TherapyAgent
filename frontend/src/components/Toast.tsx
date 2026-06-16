import { X } from 'lucide-react'

interface ToastItem {
  id: number
  message: string
  type: 'success' | 'error' | 'info'
}

interface Props {
  toasts: ToastItem[]
  onDismiss: (id: number) => void
}

const styles = {
  success: 'bg-emerald-600 text-white',
  error: 'bg-red-600 text-white',
  info: 'bg-slate-800 text-white dark:bg-slate-700',
}

export function ToastContainer({ toasts, onDismiss }: Props) {
  if (toasts.length === 0) return null

  return (
    <div
      className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 max-w-sm"
      role="region"
      aria-label="Notifications"
    >
      {toasts.map((t) => (
        <div
          key={t.id}
          className={`flex items-center gap-3 px-4 py-3 rounded-lg shadow-lg text-sm ${styles[t.type]}`}
          role="alert"
        >
          <span className="flex-1">{t.message}</span>
          <button
            onClick={() => onDismiss(t.id)}
            className="opacity-70 hover:opacity-100"
            aria-label="Dismiss notification"
          >
            <X size={16} />
          </button>
        </div>
      ))}
    </div>
  )
}
