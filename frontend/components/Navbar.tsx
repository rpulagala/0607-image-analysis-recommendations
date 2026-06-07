'use client'
import { useEffect, useState } from 'react'
import Link from 'next/link'
import { useRouter, usePathname } from 'next/navigation'
import { clearAuth, isAuthenticated } from '@/lib/auth'
import { api } from '@/lib/api'

export default function Navbar() {
  const router = useRouter()
  const pathname = usePathname()
  const [authed, setAuthed] = useState(false)

  useEffect(() => {
    setAuthed(isAuthenticated())
  }, [pathname])

  const signOut = async () => {
    try { await api.post('/auth/signout') } catch {}
    clearAuth()
    router.push('/auth/signin')
  }

  if (!authed) return null

  const link = (href: string, label: string) => (
    <Link
      href={href}
      className={`text-sm hover:text-blue-300 transition-colors ${pathname === href ? 'text-blue-300 font-medium' : 'text-white/80'}`}
    >
      {label}
    </Link>
  )

  return (
    <nav style={{ background: '#0f3460' }} className="px-6 py-4 shadow-sm">
      <div className="max-w-5xl mx-auto flex items-center justify-between">
        <Link href="/dashboard" className="text-white font-bold text-lg">
          ImageAI
        </Link>
        <div className="flex items-center gap-6">
          {link('/dashboard', 'Dashboard')}
          {link('/history', 'History')}
          {link('/profile', 'Profile')}
          <button
            onClick={signOut}
            className="text-sm bg-white/10 hover:bg-white/20 text-white px-4 py-1.5 rounded-full transition-colors"
          >
            Sign out
          </button>
        </div>
      </div>
    </nav>
  )
}
