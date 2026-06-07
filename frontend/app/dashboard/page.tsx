'use client'
import { useEffect, useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { isAuthenticated } from '@/lib/auth'
import { api } from '@/lib/api'
import Navbar from '@/components/Navbar'
import ImageUpload from '@/components/ImageUpload'
import AnalysisResult from '@/components/AnalysisResult'
import UsageMeter from '@/components/UsageMeter'
import { Analysis, UsageInfo } from '@/lib/types'

export default function DashboardPage() {
  const router = useRouter()
  const [usage, setUsage] = useState<UsageInfo | null>(null)
  const [result, setResult] = useState<Analysis | null>(null)
  const [recent, setRecent] = useState<Analysis[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!isAuthenticated()) { router.push('/auth/signin'); return }
    fetchData()
  }, [])

  const fetchData = async () => {
    const [u, h] = await Promise.allSettled([
      api.get('/api/billing/usage'),
      api.get('/api/history?limit=3'),
    ])
    if (u.status === 'fulfilled') setUsage(u.value)
    if (h.status === 'fulfilled') setRecent(h.value.items ?? [])
  }

  const handleAnalyze = async (file: File) => {
    setError('')
    setResult(null)
    setLoading(true)
    try {
      const data = await api.upload('/api/analyze', file)
      setResult(data)
      fetchData()
    } catch (err: any) {
      if (err.status === 402) {
        setError("You've reached your free tier limit. Upgrade to Pro for unlimited analyses.")
      } else {
        setError(err.message || 'Analysis failed. Please try again.')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen" style={{ background: '#f4f6f9' }}>
      <Navbar />
      <div className="max-w-3xl mx-auto px-6 py-10">
        <h1 className="text-2xl font-bold mb-1" style={{ color: '#0f3460' }}>Analyze an Image</h1>
        <p className="text-gray-500 text-sm mb-6">
          Upload an image to get AI insights and personalized recommendations.
        </p>

        {usage && (
          <div className="mb-6">
            <UsageMeter usage={usage} />
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg px-4 py-3 mb-6 flex justify-between items-center gap-4">
            <span>{error}</span>
            {error.includes('limit') && (
              <Link href="/profile" style={{ color: '#1a6ec8' }} className="text-sm font-semibold whitespace-nowrap">
                Upgrade →
              </Link>
            )}
          </div>
        )}

        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 mb-8">
          <ImageUpload onAnalyze={handleAnalyze} loading={loading} />
        </div>

        {result && <AnalysisResult result={result} />}

        {recent.length > 0 && !result && (
          <div className="mt-4">
            <div className="flex justify-between items-center mb-4">
              <h2 className="font-semibold text-gray-700">Recent Analyses</h2>
              <Link href="/history" style={{ color: '#1a6ec8' }} className="text-sm hover:underline">
                View all →
              </Link>
            </div>
            <div className="grid grid-cols-3 gap-4">
              {recent.map((item) => (
                <Link key={item.id} href={`/history/${item.id}`}>
                  <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden hover:shadow-md transition-shadow cursor-pointer">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src={item.image_url} alt="" className="w-full h-32 object-cover" />
                    <div className="p-3">
                      <p className="text-xs text-gray-500 line-clamp-2">{item.analysis?.description}</p>
                      <p className="text-xs text-gray-400 mt-1">
                        {new Date(item.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
