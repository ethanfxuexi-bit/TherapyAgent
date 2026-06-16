import { useRef, useState, useEffect } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Loader2, Sparkles } from 'lucide-react'
import { DrawingCanvas, type DrawingCanvasHandle } from '../components/DrawingCanvas'
import { ResultsPanel } from '../components/ResultsPanel'
import { RewardBadge } from '../components/RewardBadge'
import { predictMood } from '../lib/api'
import { useToast } from '../contexts/ToastContext'
import type { MoodPrediction } from '../types'

export function DashboardPage() {
  const canvasRef = useRef<DrawingCanvasHandle>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const [canvasSize, setCanvasSize] = useState({ width: 400, height: 400 })
  const [result, setResult] = useState<MoodPrediction | null>(null)
  const [notes, setNotes] = useState('')
  const { toast } = useToast()
  const queryClient = useQueryClient()

  useEffect(() => {
    const updateSize = () => {
      if (!containerRef.current) return
      const w = containerRef.current.clientWidth
      const size = Math.min(w, 480)
      setCanvasSize({ width: size, height: size })
    }
    updateSize()
    window.addEventListener('resize', updateSize)
    return () => window.removeEventListener('resize', updateSize)
  }, [])

  const mutation = useMutation({
    mutationFn: async () => {
      const blob = await canvasRef.current?.exportImage()
      if (!blob) throw new Error('Could not export drawing')
      return predictMood(blob, notes || undefined)
    },
    onSuccess: (data) => {
      setResult(data)
      queryClient.invalidateQueries({ queryKey: ['rewards'] })
      queryClient.invalidateQueries({ queryKey: ['history'] })
      toast('Analysis complete!', 'success')
    },
    onError: (err: Error) => {
      toast(err.message || 'Analysis failed', 'error')
    },
  })

  const handleAnalyze = () => {
    if (canvasRef.current?.isEmpty()) {
      toast('Draw something first', 'info')
      return
    }
    mutation.mutate()
  }

  return (
    <div className="max-w-5xl mx-auto px-4 py-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold">Draw your mood</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">Express yourself freely, then analyze</p>
        </div>
        <RewardBadge />
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        <div ref={containerRef}>
          <DrawingCanvas ref={canvasRef} width={canvasSize.width} height={canvasSize.height} />

          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Optional note about how you're feeling..."
            className="mt-3 w-full px-3 py-2 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 resize-none h-16 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            maxLength={500}
            aria-label="Journal note"
          />

          <button
            onClick={handleAnalyze}
            disabled={mutation.isPending}
            className="mt-3 w-full flex items-center justify-center gap-2 px-6 py-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl font-medium transition-colors disabled:opacity-50"
          >
            {mutation.isPending ? (
              <>
                <Loader2 className="animate-spin" size={20} />
                Analyzing...
              </>
            ) : (
              <>
                <Sparkles size={20} />
                Analyze mood
              </>
            )}
          </button>
        </div>

        <div className="rounded-xl border border-slate-200 dark:border-slate-700 bg-[var(--color-surface)] p-5 min-h-[300px]">
          {result ? (
            <ResultsPanel result={result} />
          ) : (
            <div className="h-full flex items-center justify-center text-slate-400 text-sm text-center px-4">
              Your mood analysis will appear here after you submit a drawing.
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
