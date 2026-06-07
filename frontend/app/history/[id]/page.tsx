'use client'
import { useEffect, useState } from 'react'
import Link from 'next/link'
import { useRouter, useParams } from 'next/navigation'
import { isAuthenticated } from '@/lib/auth'
import { api } from '@/lib/api'
import Navbar from '@/components/Navbar'
import AnalysisResult from '@/components/AnalysisResult'
import { Analysis } from '@/lib/types'

export default function AnalysisDetailPage() {
  const router = useRouter()
  const params = useParams()
  const [item, setItem] = useState<Analysis | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!isAuthenticated()) { router.push('/auth/signin'); return }
    api.get(`/api/history/${params.id}`)
      .then(setItem)
      .catch(() => setError('Analysis not found.'))
      .finally(() => setLoading(false))
  }, [params.id])

  return (
    <div className="min-h-screen" style={{ background: '#f4f6f9' }}>
      <Navbar />
      <div className="max-w-3xl mx-auto px-6 py-10">
        <Link href="/history" style={{ color: '#1a6ec8' }} className="text-sm hover:underline mb-6 inline-block">
          ← Back to history
        </Link>

        {loading && <div className="text-center py-20 text-gray-400">Loading...</div>}
        {error && <div className="text-center py-20 text-gray-500">{error}</div>}

        {item && (
          <>
            <div className="flex justify-between items-center mb-6">
              <h1 className="text-xl font-bold" style={{ color: '#0f3460' }}>Analysis Detail</h1>
              <span className="text-sm text-gray-400">
                {new Date(item.created_at).toLocaleString()}
              </span>
            </div>
            <AnalysisResult result={item} />
          </>
        )}
      </div>
    </div>
  )
}
