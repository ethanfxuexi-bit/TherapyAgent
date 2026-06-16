import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Line } from 'react-chartjs-2'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Legend,
} from 'chart.js'
import { Download, Trash2, Loader2 } from 'lucide-react'
import { clearHistory, deleteHistoryEntry, exportHistoryCsv, getHistory } from '../lib/api'
import { useToast } from '../contexts/ToastContext'
import { MOOD_COLORS, MOOD_EMOJI, MOODS, type MoodName } from '../types'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend)

const MOOD_VALUE: Record<MoodName, number> = {
  Happy: 5,
  Excited: 4,
  Calm: 3,
  Anxious: 2,
  Sad: 1,
  Angry: 0,
}

export function HistoryPage() {
  const [moodFilter, setMoodFilter] = useState<string>('')
  const { toast } = useToast()
  const queryClient = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ['history', moodFilter],
    queryFn: () => getHistory({ limit: 100, mood: moodFilter || undefined }),
  })

  const deleteMutation = useMutation({
    mutationFn: deleteHistoryEntry,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['history'] })
      toast('Entry deleted', 'success')
    },
    onError: () => toast('Delete failed', 'error'),
  })

  const clearMutation = useMutation({
    mutationFn: clearHistory,
    onSuccess: (res) => {
      queryClient.invalidateQueries({ queryKey: ['history'] })
      toast(`Cleared ${res.deleted_count} entries`, 'success')
    },
    onError: () => toast('Clear failed', 'error'),
  })

  const items = data?.items ?? []

  const moodCounts = MOODS.reduce(
    (acc, m) => {
      acc[m] = items.filter((i) => i.mood === m).length
      return acc
    },
    {} as Record<MoodName, number>,
  )

  const trendData = [...items].reverse().slice(-30)

  return (
    <div className="max-w-5xl mx-auto px-4 py-6 space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-semibold">Mood history</h1>
          <p className="text-sm text-slate-500">{data?.total ?? 0} entries</p>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={moodFilter}
            onChange={(e) => setMoodFilter(e.target.value)}
            className="text-sm px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800"
            aria-label="Filter by mood"
          >
            <option value="">All moods</option>
            {MOODS.map((m) => (
              <option key={m} value={m}>{MOOD_EMOJI[m]} {m}</option>
            ))}
          </select>
          <button
            onClick={() => exportHistoryCsv(items)}
            disabled={items.length === 0}
            className="flex items-center gap-1 px-3 py-1.5 text-sm rounded-lg border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800 disabled:opacity-30"
          >
            <Download size={16} /> CSV
          </button>
          <button
            onClick={() => {
              if (confirm('Delete all history? This cannot be undone.')) clearMutation.mutate()
            }}
            disabled={items.length === 0}
            className="flex items-center gap-1 px-3 py-1.5 text-sm rounded-lg text-red-600 border border-red-200 dark:border-red-900 hover:bg-red-50 dark:hover:bg-red-900/20 disabled:opacity-30"
          >
            <Trash2 size={16} /> Clear all
          </button>
        </div>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-12">
          <Loader2 className="animate-spin text-indigo-500" size={32} />
        </div>
      ) : items.length === 0 ? (
        <div className="text-center py-16 text-slate-400">
          No mood entries yet. Draw something on the dashboard!
        </div>
      ) : (
        <>
          <div className="grid md:grid-cols-3 gap-4">
            <div className="md:col-span-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-[var(--color-surface)] p-4">
              <h2 className="text-sm font-medium mb-3 text-slate-600 dark:text-slate-400">Trend</h2>
              <Line
                data={{
                  labels: trendData.map((e) =>
                    new Date(e.timestamp).toLocaleDateString(undefined, { month: 'short', day: 'numeric' }),
                  ),
                  datasets: [
                    {
                      label: 'Mood level',
                      data: trendData.map((e) => MOOD_VALUE[e.mood]),
                      borderColor: '#6366f1',
                      backgroundColor: '#6366f180',
                      tension: 0.3,
                      fill: true,
                    },
                  ],
                }}
                options={{
                  responsive: true,
                  scales: {
                    y: {
                      min: 0,
                      max: 5,
                      ticks: {
                        callback: (v) => {
                          const map = ['Angry', 'Sad', 'Anxious', 'Calm', 'Excited', 'Happy']
                          return map[v as number] ?? ''
                        },
                      },
                    },
                  },
                  plugins: { legend: { display: false } },
                }}
              />
            </div>

            <div className="rounded-xl border border-slate-200 dark:border-slate-700 bg-[var(--color-surface)] p-4">
              <h2 className="text-sm font-medium mb-3 text-slate-600 dark:text-slate-400">Distribution</h2>
              <ul className="space-y-2">
                {MOODS.map((m) => (
                  <li key={m} className="flex items-center gap-2 text-sm">
                    <span>{MOOD_EMOJI[m]}</span>
                    <span className="flex-1">{m}</span>
                    <span className="font-medium">{moodCounts[m]}</span>
                    <div className="w-16 h-2 bg-slate-100 dark:bg-slate-700 rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full"
                        style={{
                          width: items.length ? `${(moodCounts[m] / items.length) * 100}%` : '0%',
                          backgroundColor: MOOD_COLORS[m],
                        }}
                      />
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          <div className="rounded-xl border border-slate-200 dark:border-slate-700 overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-slate-50 dark:bg-slate-800/50">
                <tr>
                  <th className="text-left px-4 py-2 font-medium">Date</th>
                  <th className="text-left px-4 py-2 font-medium">Mood</th>
                  <th className="text-left px-4 py-2 font-medium">Confidence</th>
                  <th className="text-left px-4 py-2 font-medium">Note</th>
                  <th className="px-4 py-2"></th>
                </tr>
              </thead>
              <tbody>
                {items.map((entry) => (
                  <tr key={entry.id} className="border-t border-slate-100 dark:border-slate-800">
                    <td className="px-4 py-3 text-slate-500">
                      {new Date(entry.timestamp).toLocaleString()}
                    </td>
                    <td className="px-4 py-3">
                      <span style={{ color: MOOD_COLORS[entry.mood] }}>
                        {MOOD_EMOJI[entry.mood]} {entry.mood}
                      </span>
                    </td>
                    <td className="px-4 py-3">{Math.round(entry.confidence * 100)}%</td>
                    <td className="px-4 py-3 text-slate-500 truncate max-w-[150px]">{entry.notes || '—'}</td>
                    <td className="px-4 py-3">
                      <button
                        onClick={() => deleteMutation.mutate(entry.id)}
                        className="text-red-500 hover:text-red-700"
                        aria-label={`Delete entry from ${entry.timestamp}`}
                      >
                        <Trash2 size={16} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  )
}
