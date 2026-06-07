'use client'
import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { isAuthenticated } from '@/lib/auth'
import { api } from '@/lib/api'
import Navbar from '@/components/Navbar'
import UsageMeter from '@/components/UsageMeter'
import { UserProfile, UsageInfo } from '@/lib/types'

const PRO_PRICE_ID = process.env.NEXT_PUBLIC_STRIPE_PRO_PRICE_ID || 'price_placeholder'

export default function ProfilePage() {
  const router = useRouter()
  const [profile, setProfile] = useState<UserProfile | null>(null)
  const [usage, setUsage] = useState<UsageInfo | null>(null)
  const [fullName, setFullName] = useState('')
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')

  useEffect(() => {
    if (!isAuthenticated()) { router.push('/auth/signin'); return }
    Promise.all([api.get('/api/profile'), api.get('/api/billing/usage')]).then(([p, u]) => {
      setProfile(p)
      setFullName(p.full_name ?? '')
      setUsage(u)
    })
  }, [])

  const saveProfile = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    setMessage('')
    try {
      await api.patch('/api/profile', { full_name: fullName })
      setMessage('Saved!')
    } catch {
      setMessage('Failed to save.')
    } finally {
      setSaving(false)
    }
  }

  const openBillingPortal = async () => {
    try {
      const { url } = await api.post('/api/billing/portal', { return_url: window.location.href })
      window.location.href = url
    } catch {
      alert('Could not open billing portal. Please try again.')
    }
  }

  const startCheckout = async () => {
    try {
      const { url } = await api.post('/api/billing/checkout', {
        price_id: PRO_PRICE_ID,
        success_url: `${window.location.origin}/profile?upgraded=true`,
        cancel_url: window.location.href,
      })
      window.location.href = url
    } catch {
      alert('Could not open checkout. Please try again.')
    }
  }

  return (
    <div className="min-h-screen" style={{ background: '#f4f6f9' }}>
      <Navbar />
      <div className="max-w-2xl mx-auto px-6 py-10 space-y-6">
        <h1 className="text-2xl font-bold" style={{ color: '#0f3460' }}>Account</h1>

        {/* Profile */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <h2 className="font-semibold text-gray-700 mb-4">Profile</h2>
          {profile && (
            <form onSubmit={saveProfile} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-600 mb-1">Email</label>
                <input
                  value={profile.email}
                  disabled
                  className="w-full bg-gray-50 border border-gray-200 rounded-lg px-3 py-2.5 text-sm text-gray-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-600 mb-1">Full name</label>
                <input
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:border-blue-400"
                  placeholder="Your name"
                />
              </div>
              <div className="flex items-center gap-3">
                <button
                  type="submit"
                  disabled={saving}
                  style={{ background: '#1a6ec8' }}
                  className="text-white px-5 py-2 rounded-lg text-sm font-semibold hover:opacity-90 disabled:opacity-50"
                >
                  {saving ? 'Saving...' : 'Save'}
                </button>
                {message && (
                  <span className={`text-sm ${message === 'Saved!' ? 'text-green-600' : 'text-red-500'}`}>
                    {message}
                  </span>
                )}
              </div>
            </form>
          )}
        </div>

        {/* Usage */}
        {usage && (
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <h2 className="font-semibold text-gray-700 mb-4">Usage this month</h2>
            <UsageMeter usage={usage} />
          </div>
        )}

        {/* Subscription */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <h2 className="font-semibold text-gray-700 mb-4">Subscription</h2>
          {usage?.tier === 'pro' ? (
            <div className="flex items-center justify-between">
              <div>
                <span
                  style={{ background: '#f0f6ff', color: '#1a6ec8' }}
                  className="text-sm font-semibold px-3 py-1 rounded-full"
                >
                  Pro Plan
                </span>
                <p className="text-sm text-gray-500 mt-2">Unlimited analyses per month.</p>
              </div>
              <button
                onClick={openBillingPortal}
                className="text-sm border border-gray-300 text-gray-600 px-4 py-2 rounded-lg hover:bg-gray-50"
              >
                Manage billing
              </button>
            </div>
          ) : (
            <div className="flex items-center justify-between gap-4">
              <div>
                <span className="text-sm bg-gray-100 text-gray-600 px-3 py-1 rounded-full font-medium">
                  Free Plan
                </span>
                <p className="text-sm text-gray-500 mt-2">5 analyses per month. Upgrade for unlimited.</p>
              </div>
              <button
                onClick={startCheckout}
                style={{ background: '#1a6ec8' }}
                className="text-white text-sm px-5 py-2.5 rounded-lg font-semibold hover:opacity-90 whitespace-nowrap"
              >
                Upgrade to Pro
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
