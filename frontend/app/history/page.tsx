'use client'
import { useEffect, useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { isAuthenticated } from '@/lib/auth'
import { api } from '@/lib/api'
import Navbar from '@/components/Navbar'
import { Analysis } from '@/lib/types'

export default function HistoryPage() {
  const router = useRouter()
  const [items, setItems] = useState<Analysis[]>([])
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(true)
  const [hasMore, setHasMore] = useState(false)

  useEffect(() => {
    if (!isAuthenticated()) { router.push('/auth/signin'); return }
    fetchHistory(1)
  }, [])

  const fetchHistory = async (p: number) => {
    setLoading(true)
    try {
      const data = await api.get(`/api/history?page=${p}&limit=12`)
      setItems((prev) => p === 1 ? data.items : [...prev, ...data.items])
      setHasMore(data.items.length === 12)
      setPage(p)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen" style={{ background: '#f4f6f9' }}>
      <Navbar />
      <div className="max-w-5xl mx-auto px-6 py-10">
        <h1 className="text-2xl font-bold mb-6" style={{ color: '#0f3460' }}>Analysis History</h1>

        {loading && items.length === 0 && (
          <div className="text-center py-20 text-gray-400">Loading...</div>
        )}

        {!loading && items.length === 0 && (
          <div className="text-center py-20">
            <div className="text-5xl mb-4">🖼️</div>
            <p className="text-gray-500 mb-2">No analyses yet.</p>
            <Link href="/dashboard" style={{ color: '#1a6ec8' }} className="text-sm font-medium hover:underline">
              Analyze your first image →
            </Link>
          </div>
        )}

        {items.length > 0 && (
          <>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
              {items.map((item) => (
                <Link key={item.id} href={`/history/${item.id}`}>
                  <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden hover:shadow-md transition-shadow cursor-pointer">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src={item.image_url} alt="" className="w-full h-40 object-cover" />
                    <div className="p-3">
                      <p className="text-xs text-gray-500 line-clamp-2">{item.analysis?.description}</p>
                      <p className="text-xs text-gray-400 mt-1.5">
                        {new Date(item.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                </Link>
              ))}
            </div>

            {hasMore && (
              <div className="text-center mt-8">
                <button
                  onClick={() => fetchHistory(page + 1)}
                  disabled={loading}
                  className="border border-gray-300 text-gray-600 px-6 py-2.5 rounded-lg text-sm hover:bg-gray-50 disabled:opacity-50"
                >
                  {loading ? 'Loading...' : 'Load more'}
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
