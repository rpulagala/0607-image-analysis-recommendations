'use client'
import { Analysis } from '@/lib/types'

export default function AnalysisResult({ result }: { result: Analysis }) {
  const { analysis, recommendations, image_url } = result

  return (
    <div className="space-y-5">
      {/* Image + labels + description */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={image_url} alt="Analyzed" className="w-full object-cover" style={{ maxHeight: 320 }} />
        <div className="p-5">
          <div className="flex flex-wrap gap-2 mb-3">
            {analysis.labels.map((label) => (
              <span
                key={label}
                style={{ background: '#f0f6ff', color: '#1a6ec8' }}
                className="text-xs px-3 py-1 rounded-full font-medium"
              >
                {label}
              </span>
            ))}
          </div>
          <p className="text-gray-700 text-sm leading-relaxed">{analysis.description}</p>
        </div>
      </div>

      {/* Objects + Attributes */}
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
          <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
            Objects Detected
          </h3>
          <div className="flex flex-wrap gap-2">
            {analysis.objects.map((obj) => (
              <span key={obj} className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">
                {obj}
              </span>
            ))}
          </div>
        </div>
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
          <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
            Attributes
          </h3>
          <dl className="space-y-1">
            {Object.entries(analysis.attributes).map(([k, v]) => (
              <div key={k} className="flex gap-2 text-xs">
                <dt className="text-gray-400 capitalize">{k}:</dt>
                <dd className="text-gray-700 font-medium">{v}</dd>
              </div>
            ))}
          </dl>
        </div>
      </div>

      {/* Recommendations */}
      <div>
        <h3 className="font-semibold text-gray-800 mb-3">Personalized Recommendations</h3>
        <div className="space-y-3">
          {recommendations.map((rec, i) => (
            <div key={i} className="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
              <div className="flex items-start justify-between gap-4">
                <div className="min-w-0">
                  <h4 className="font-semibold text-gray-800 text-sm">{rec.title}</h4>
                  <p className="text-gray-500 text-sm mt-1">{rec.description}</p>
                </div>
                <div className="text-right flex-shrink-0">
                  <div className="text-xs text-gray-400 mb-1">
                    {Math.round(rec.relevance_score * 100)}% match
                  </div>
                  <div className="w-16 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                    <div
                      style={{ width: `${rec.relevance_score * 100}%`, background: '#1a6ec8' }}
                      className="h-full rounded-full"
                    />
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
