import type { MoodPrediction } from '../types'
import { MOOD_COLORS, MOOD_EMOJI } from '../types'
import { MoodBreakdownChart } from './MoodBreakdownChart'

interface Props {
  result: MoodPrediction
}

export function ResultsPanel({ result }: Props) {
  const pct = Math.round(result.confidence * 100)

  return (
    <div className="space-y-4">
      <div className="text-center py-4">
        <div className="text-5xl mb-2" aria-hidden>
          {MOOD_EMOJI[result.mood]}
        </div>
        <h2 className="text-2xl font-semibold" style={{ color: MOOD_COLORS[result.mood] }}>
          {result.mood}
        </h2>
        <p className="text-slate-500 dark:text-slate-400 mt-1">{pct}% confidence</p>
      </div>

      <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed bg-slate-50 dark:bg-slate-800/50 rounded-lg p-3">
        {result.analysis_details.explanation}
      </p>

      {result.analysis_details.dominant_colors && result.analysis_details.dominant_colors.length > 0 && (
        <p className="text-xs text-slate-500">
          Dominant colors: {result.analysis_details.dominant_colors.join(', ')}
        </p>
      )}

      <div>
        <h3 className="text-sm font-medium mb-2 text-slate-700 dark:text-slate-300">All moods</h3>
        <MoodBreakdownChart scores={result.scores} highlight={result.mood} />
      </div>
    </div>
  )
}
