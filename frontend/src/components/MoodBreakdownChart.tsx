import { Bar } from 'react-chartjs-2'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Tooltip,
  Legend,
} from 'chart.js'
import type { MoodScores, MoodName } from '../types'
import { MOOD_COLORS, MOOD_EMOJI, MOODS } from '../types'

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip, Legend)

interface Props {
  scores: MoodScores
  highlight?: MoodName
}

export function MoodBreakdownChart({ scores, highlight }: Props) {
  const labels = MOODS.map((m) => `${MOOD_EMOJI[m]} ${m}`)
  const data = MOODS.map((m) => Math.round(scores[m] * 100))

  return (
    <div role="img" aria-label="Mood breakdown chart">
      <Bar
        data={{
          labels,
          datasets: [
            {
              label: 'Probability %',
              data,
              backgroundColor: MOODS.map((m) =>
                m === highlight ? MOOD_COLORS[m] : MOOD_COLORS[m] + '99',
              ),
              borderRadius: 6,
            },
          ],
        }}
        options={{
          responsive: true,
          plugins: {
            legend: { display: false },
            tooltip: {
              callbacks: {
                label: (ctx) => `${ctx.parsed.y}%`,
              },
            },
          },
          scales: {
            y: {
              beginAtZero: true,
              max: 100,
              ticks: { callback: (v) => `${v}%` },
              grid: { color: 'rgba(148,163,184,0.2)' },
            },
            x: {
              grid: { display: false },
            },
          },
        }}
      />
    </div>
  )
}
