export interface AnalysisResult {
  labels: string[]
  description: string
  objects: string[]
  attributes: Record<string, string>
}

export interface Recommendation {
  title: string
  description: string
  relevance_score: number
}

export interface Analysis {
  id: string
  image_url: string
  analysis: AnalysisResult
  recommendations: Recommendation[]
  created_at: string
}

export interface UserProfile {
  id: string
  email: string
  full_name: string | null
  subscription_tier: 'free' | 'pro'
  analyses_this_month: number
}

export interface UsageInfo {
  tier: 'free' | 'pro'
  used: number
  limit: number | null
}
