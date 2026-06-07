'use client'
import Link from 'next/link'
import { UsageInfo } from '@/lib/types'

export default function UsageMeter({ usage }: { usage: UsageInfo }) {
  if (usage.tier === 'pro') {
    return (
      <div
        style={{ background: '#f0f6ff', borderColor: '#bdd5f8' }}
        className="border rounded-lg px-4 py-3 flex items-center justify-between"
      >
        <div className="flex items-center gap-2">
          <span style={{ color: '#1a6ec8' }} className="font-semibold text-sm">✦ Pro Plan</span>
          <span className="text-gray-500 text-sm">— Unlimited analyses</span>
        </div>
        <Link href="/profile" style={{ color: '#1a6ec8' }} className="text-xs hover:underline">
          Manage
        </Link>
      </div>
    )
  }

  const used = usage.used
  const limit = usage.limit ?? 5
  const pct = Math.min((used / limit) * 100, 100)
  const atLimit = used >= limit

  return (
    <div className={`rounded-lg px-4 py-3 border ${atLimit ? 'bg-red-50 border-red-200' : 'bg-gray-50 border-gray-200'}`}>
      <div className="flex justify-between items-center mb-2">
        <span className="text-sm font-medium text-gray-700">Free tier</span>
        <span className={`text-sm font-semibold ${atLimit ? 'text-red-600' : 'text-gray-600'}`}>
          {used} / {limit} analyses
        </span>
      </div>
      <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all ${atLimit ? 'bg-red-500' : 'bg-blue-500'}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      {atLimit && (
        <div className="mt-2 flex items-center justify-between">
          <span className="text-xs text-red-600">Monthly limit reached</span>
          <Link
            href="/profile"
            style={{ background: '#1a6ec8' }}
            className="text-xs text-white px-3 py-1 rounded-full hover:opacity-90"
          >
            Upgrade to Pro
          </Link>
        </div>
      )}
    </div>
  )
}
