import Link from 'next/link'

const features = [
  {
    icon: '🔍',
    title: 'Deep Image Analysis',
    desc: 'GPT-4o Vision detects objects, scenes, attributes, and mood in any image.',
  },
  {
    icon: '✦',
    title: 'Personalized Recommendations',
    desc: 'AI generates 5 tailored suggestions based on exactly what is in your image.',
  },
  {
    icon: '📋',
    title: 'Full History',
    desc: 'All your past analyses saved and searchable, ready to revisit any time.',
  },
]

const freeTier = ['5 analyses / month', 'AI image analysis', 'Personalized recommendations', 'Analysis history']
const proTier = [...freeTier, 'Priority support']

export default function LandingPage() {
  return (
    <main className="min-h-screen bg-white">
      {/* Nav */}
      <nav style={{ background: '#0f3460' }} className="px-6 py-4">
        <div className="max-w-5xl mx-auto flex justify-between items-center">
          <span className="text-white font-bold text-xl">ImageAI</span>
          <div className="flex gap-4 items-center">
            <Link href="/auth/signin" className="text-white/80 hover:text-white text-sm">
              Sign in
            </Link>
            <Link
              href="/auth/signup"
              style={{ background: '#1a6ec8' }}
              className="text-white text-sm px-4 py-2 rounded-lg hover:opacity-90"
            >
              Get started
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section
        className="py-24 px-6 text-center"
        style={{ background: 'linear-gradient(135deg, #0f3460, #1a6ec8)' }}
      >
        <h1 className="text-5xl font-bold text-white mb-6 leading-tight">
          Upload any image.<br />Get AI-powered insights instantly.
        </h1>
        <p className="text-xl text-blue-100 mb-10 max-w-2xl mx-auto">
          Our AI analyzes your images and delivers personalized recommendations tailored to what it sees.
        </p>
        <Link
          href="/auth/signup"
          className="bg-white font-bold px-8 py-4 rounded-xl text-lg hover:shadow-lg inline-block"
          style={{ color: '#0f3460' }}
        >
          Start for free →
        </Link>
        <p className="text-blue-200 text-sm mt-4">5 free analyses per month. No credit card required.</p>
      </section>

      {/* Features */}
      <section className="py-20 px-6" style={{ background: '#f4f6f9' }}>
        <div className="max-w-5xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-8">
          {features.map((f) => (
            <div key={f.title} className="bg-white rounded-xl p-6 shadow-sm">
              <div className="text-4xl mb-4">{f.icon}</div>
              <h3 className="font-bold text-gray-800 text-lg mb-2">{f.title}</h3>
              <p className="text-gray-500 text-sm leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Pricing */}
      <section className="py-20 px-6">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-3xl font-bold text-gray-800 mb-12 text-center">Simple pricing</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Free */}
            <div className="border border-gray-200 rounded-xl p-8">
              <h3 className="text-xl font-bold mb-2 text-gray-800">Free</h3>
              <div className="text-4xl font-bold text-gray-800 mb-6">$0</div>
              <ul className="text-sm text-gray-600 space-y-3 mb-8">
                {freeTier.map((f) => (
                  <li key={f} className="flex gap-2 items-center">
                    <span className="text-green-500">✓</span>
                    {f}
                  </li>
                ))}
              </ul>
              <Link
                href="/auth/signup"
                className="block text-center border border-gray-300 rounded-lg py-2.5 text-sm hover:bg-gray-50"
              >
                Get started free
              </Link>
            </div>

            {/* Pro */}
            <div
              style={{ borderColor: '#1a6ec8', background: '#f0f6ff' }}
              className="border-2 rounded-xl p-8 relative"
            >
              <span
                style={{ background: '#1a6ec8' }}
                className="absolute -top-3 left-1/2 -translate-x-1/2 text-white text-xs font-bold px-4 py-1 rounded-full"
              >
                RECOMMENDED
              </span>
              <h3 className="text-xl font-bold mb-2" style={{ color: '#0f3460' }}>Pro</h3>
              <div className="text-4xl font-bold mb-1" style={{ color: '#0f3460' }}>$X</div>
              <div className="text-sm text-gray-500 mb-5">/month</div>
              <ul className="text-sm text-gray-600 space-y-3 mb-8">
                {proTier.map((f) => (
                  <li key={f} className="flex gap-2 items-center">
                    <span className="text-green-500">✓</span>
                    {f}
                  </li>
                ))}
              </ul>
              <Link
                href="/auth/signup"
                style={{ background: '#1a6ec8' }}
                className="block text-center text-white rounded-lg py-2.5 text-sm hover:opacity-90"
              >
                Upgrade to Pro
              </Link>
            </div>
          </div>
        </div>
      </section>

      <footer style={{ background: '#0f3460' }} className="py-8 px-6 text-center text-white/60 text-sm">
        © 2026 ImageAI
      </footer>
    </main>
  )
}
