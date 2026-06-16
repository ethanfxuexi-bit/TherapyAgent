import { useQuery } from '@tanstack/react-query'
import { Flame, Coins } from 'lucide-react'
import { getRewardsStatus } from '../lib/api'

export function RewardBadge() {
  const { data } = useQuery({
    queryKey: ['rewards'],
    queryFn: getRewardsStatus,
    refetchInterval: 60000,
  })

  if (!data) return null

  return (
    <div className="flex items-center gap-3 text-sm">
      <span className="flex items-center gap-1 text-amber-600 dark:text-amber-400" title="Coins">
        <Coins size={16} aria-hidden />
        {data.coins}
      </span>
      <span className="flex items-center gap-1 text-orange-500" title="Daily streak">
        <Flame size={16} aria-hidden />
        {data.streak} day{data.streak !== 1 ? 's' : ''}
      </span>
    </div>
  )
}
