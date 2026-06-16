export const MOODS = ['Happy', 'Sad', 'Calm', 'Angry', 'Anxious', 'Excited'] as const
export type MoodName = (typeof MOODS)[number]

export interface MoodScores {
  Happy: number
  Sad: number
  Calm: number
  Angry: number
  Anxious: number
  Excited: number
}

export interface AnalysisDetails {
  method: string
  model: string
  device: string
  explanation: string
  dominant_colors?: string[]
  top_prompts?: string[]
}

export interface MoodPrediction {
  mood: MoodName
  confidence: number
  scores: MoodScores
  analysis_details: AnalysisDetails
  history_id: string | null
}

export interface HistoryEntry {
  id: string
  user_id: string
  timestamp: string
  mood: MoodName
  confidence: number
  scores: MoodScores
  thumbnail_url?: string | null
  notes?: string | null
  analysis_details?: AnalysisDetails | null
}

export interface HistoryListResponse {
  items: HistoryEntry[]
  total: number
  limit: number
  offset: number
}

export interface RewardsStatus {
  coins: number
  streak: number
  last_earned: string | null
  can_claim_today: boolean
}

export const MOOD_COLORS: Record<MoodName, string> = {
  Happy: '#fbbf24',
  Sad: '#60a5fa',
  Calm: '#34d399',
  Angry: '#f87171',
  Anxious: '#a78bfa',
  Excited: '#fb923c',
}

export const MOOD_EMOJI: Record<MoodName, string> = {
  Happy: '😊',
  Sad: '😢',
  Calm: '😌',
  Angry: '😠',
  Anxious: '😰',
  Excited: '🤩',
}
