'use client'
import { useRef, useState } from 'react'

interface Props {
  onAnalyze: (file: File) => void
  loading: boolean
}

const ACCEPTED_TYPES = ['image/jpeg', 'image/png', 'image/webp']
const MAX_BYTES = 10 * 1024 * 1024

export default function ImageUpload({ onAnalyze, loading }: Props) {
  const [preview, setPreview] = useState<string | null>(null)
  const [file, setFile] = useState<File | null>(null)
  const [drag, setDrag] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  const handleFile = (f: File) => {
    if (!ACCEPTED_TYPES.includes(f.type)) {
      alert('Only JPEG, PNG, and WEBP images are supported.')
      return
    }
    if (f.size > MAX_BYTES) {
      alert('Image must be under 10 MB.')
      return
    }
    setFile(f)
    setPreview(URL.createObjectURL(f))
  }

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setDrag(false)
    const f = e.dataTransfer.files[0]
    if (f) handleFile(f)
  }

  const onChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0]
    if (f) handleFile(f)
  }

  const reset = () => {
    setFile(null)
    setPreview(null)
    if (inputRef.current) inputRef.current.value = ''
  }

  if (!preview) {
    return (
      <div
        onDrop={onDrop}
        onDragOver={(e) => { e.preventDefault(); setDrag(true) }}
        onDragLeave={() => setDrag(false)}
        onClick={() => inputRef.current?.click()}
        className={`border-2 border-dashed rounded-xl p-14 text-center cursor-pointer transition-colors ${
          drag ? 'border-blue-400 bg-blue-50' : 'border-gray-300 hover:border-blue-400 hover:bg-blue-50/40'
        }`}
      >
        <div className="text-5xl mb-3">🖼️</div>
        <p className="text-gray-600 font-medium">Drag & drop your image here</p>
        <p className="text-gray-400 text-sm mt-1">or click to browse</p>
        <p className="text-gray-400 text-xs mt-3">JPEG · PNG · WEBP · Max 10 MB</p>
        <input
          ref={inputRef}
          type="file"
          accept="image/jpeg,image/png,image/webp"
          className="hidden"
          onChange={onChange}
        />
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="rounded-xl overflow-hidden bg-gray-100" style={{ maxHeight: 400 }}>
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={preview} alt="Preview" className="w-full object-contain" style={{ maxHeight: 400 }} />
      </div>
      <div className="flex gap-3">
        <button
          onClick={() => file && onAnalyze(file)}
          disabled={loading}
          style={{ background: '#1a6ec8' }}
          className="flex-1 text-white py-3 rounded-lg font-semibold hover:opacity-90 disabled:opacity-50 transition-opacity"
        >
          {loading ? (
            <span className="flex items-center justify-center gap-2">
              <span className="inline-block w-4 h-4 border-2 border-white/40 border-t-white rounded-full animate-spin" />
              Analyzing...
            </span>
          ) : (
            '✦ Analyze Image'
          )}
        </button>
        <button
          onClick={reset}
          disabled={loading}
          className="px-4 py-3 rounded-lg border border-gray-300 text-gray-600 hover:bg-gray-50 disabled:opacity-50"
        >
          Change
        </button>
      </div>
    </div>
  )
}
