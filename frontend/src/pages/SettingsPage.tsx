import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Moon, Sun, Trash2 } from 'lucide-react'
import { clearHistory } from '../lib/api'
import { useTheme } from '../contexts/ThemeContext'
import { useToast } from '../contexts/ToastContext'

export function SettingsPage() {
  const { theme, toggleTheme } = useTheme()
  const { toast } = useToast()
  const queryClient = useQueryClient()

  const clearMutation = useMutation({
    mutationFn: clearHistory,
    onSuccess: (res) => {
      queryClient.invalidateQueries({ queryKey: ['history'] })
      toast(`Deleted ${res.deleted_count} history entries`, 'success')
    },
    onError: () => toast('Failed to delete data', 'error'),
  })

  return (
    <div className="max-w-lg mx-auto px-4 py-6 space-y-6">
      <h1 className="text-xl font-semibold">Settings</h1>

      <section className="rounded-xl border border-slate-200 dark:border-slate-700 bg-[var(--color-surface)] p-4 space-y-4">
        <h2 className="text-sm font-medium text-slate-600 dark:text-slate-400">Appearance</h2>
        <button
          onClick={toggleTheme}
          className="flex items-center gap-3 w-full px-4 py-3 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
        >
          {theme === 'dark' ? <Sun size={20} /> : <Moon size={20} />}
          <span>{theme === 'dark' ? 'Light mode' : 'Dark mode'}</span>
        </button>
      </section>

      <section className="rounded-xl border border-slate-200 dark:border-slate-700 bg-[var(--color-surface)] p-4 space-y-4">
        <h2 className="text-sm font-medium text-slate-600 dark:text-slate-400">Privacy</h2>
        <p className="text-sm text-slate-500 leading-relaxed">
          Drawings are uploaded to our server for AI analysis. Thumbnails and mood data are stored
          in your account until you delete them. Analysis uses CLIP-based image understanding.
        </p>
      </section>

      <section className="rounded-xl border border-red-200 dark:border-red-900/50 bg-[var(--color-surface)] p-4 space-y-4">
        <h2 className="text-sm font-medium text-red-600">Danger zone</h2>
        <button
          onClick={() => {
            if (confirm('Delete all your mood history? This cannot be undone.')) {
              clearMutation.mutate()
            }
          }}
          disabled={clearMutation.isPending}
          className="flex items-center gap-2 px-4 py-2 text-sm text-red-600 border border-red-200 dark:border-red-900 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 disabled:opacity-50"
        >
          <Trash2 size={16} />
          Delete all my data
        </button>
      </section>
    </div>
  )
}
