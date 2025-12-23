'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'

const GEOGRAPHY_OPTIONS = [
  'North America',
  'European Union',
  'United Kingdom',
  'Asia Pacific',
  'Latin America',
  'Middle East & Africa',
  'Global',
  'Other'
]

const CUSTOMER_TYPE_OPTIONS = [
  'Consumer',
  'SMB',
  'Enterprise',
  'Government',
  'Mixed'
]

const BUSINESS_MODEL_OPTIONS = [
  'SaaS',
  'Marketplace',
  'Usage-based',
  'Services',
  'Hybrid'
]

const EXAMPLE_DATA = {
  idea: 'AI-powered personal finance management app that helps consumers optimize savings and investments with automated recommendations',
  industry: 'FinTech',
  geography: 'European Union',
  customer_type: 'Consumer',
  business_model: 'SaaS',
  price_assumption: '9.99',
  notes: 'Focus on GDPR compliance and multi-currency support. Target users aged 25-45 with disposable income.'
}

export default function Home() {
  const router = useRouter()
  const [formData, setFormData] = useState({
    idea: '',
    industry: '',
    geography: '',
    customer_type: '',
    business_model: '',
    price_assumption: '',
    notes: '',
  })
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [isLoading, setIsLoading] = useState(false)

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target
    setFormData(prev => ({ ...prev, [name]: value }))
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => {
        const newErrors = { ...prev }
        delete newErrors[name]
        return newErrors
      })
    }
  }

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {}

    if (!formData.idea.trim()) {
      newErrors.idea = 'Startup idea is required'
    }

    if (!formData.industry.trim()) {
      newErrors.industry = 'Industry is required'
    }

    if (!formData.geography) {
      newErrors.geography = 'Geography is required'
    }

    if (!formData.customer_type) {
      newErrors.customer_type = 'Customer type is required'
    }

    if (!formData.business_model) {
      newErrors.business_model = 'Business model is required'
    }

    if (formData.price_assumption && isNaN(parseFloat(formData.price_assumption))) {
      newErrors.price_assumption = 'Price assumption must be a valid number'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!validateForm()) {
      return
    }

    setIsLoading(true)

    try {
      // Store form data in localStorage to pass to report page
      const requestData = {
        ...formData,
        price_assumption: formData.price_assumption ? parseFloat(formData.price_assumption) : null,
        debug: false,
      }
      localStorage.setItem('atlas_request', JSON.stringify(requestData))
      
      // Navigate to report page
      router.push('/report')
    } catch (err) {
      console.error('Error storing request:', err)
      setIsLoading(false)
    }
  }

  const handleTryExample = () => {
    setFormData(EXAMPLE_DATA)
    setErrors({})
  }

  return (
    <div className="min-h-screen bg-white">
      {/* Hero Section */}
      <div className="bg-gradient-to-b from-gray-50 to-white border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-6 py-20 text-center">
          <h1 className="text-6xl font-bold text-gray-900 mb-6 tracking-tight">
            ATLAS
          </h1>
          <p className="text-2xl text-gray-600 font-medium mb-4 max-w-2xl mx-auto">
            Decision Intelligence for Market Viability
          </p>
          <p className="text-lg text-gray-500 max-w-xl mx-auto">
            Evaluate startup market viability under uncertainty with evidence-based analysis, 
            scenario modeling, and comprehensive risk assessment.
          </p>
        </div>
      </div>

      {/* Form Section */}
      <div className="max-w-3xl mx-auto px-6 py-16">
        <form onSubmit={handleSubmit} className="space-y-8">
          {/* Try Example Button */}
          <div className="flex justify-end">
            <button
              type="button"
              onClick={handleTryExample}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Try an example →
            </button>
          </div>

          {/* Idea */}
          <div>
            <label htmlFor="idea" className="block text-sm font-semibold text-gray-900 mb-2">
              Startup Idea <span className="text-red-500">*</span>
            </label>
            <textarea
              id="idea"
              name="idea"
              required
              rows={5}
              value={formData.idea}
              onChange={handleChange}
              className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-gray-900 focus:border-transparent resize-none text-gray-900 ${
                errors.idea ? 'border-red-500' : 'border-gray-300'
              }`}
              placeholder="Describe your startup idea in detail..."
            />
            {errors.idea && (
              <p className="mt-1 text-sm text-red-600">{errors.idea}</p>
            )}
          </div>

          {/* Industry */}
          <div>
            <label htmlFor="industry" className="block text-sm font-semibold text-gray-900 mb-2">
              Industry <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              id="industry"
              name="industry"
              required
              value={formData.industry}
              onChange={handleChange}
              className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-gray-900 focus:border-transparent text-gray-900 ${
                errors.industry ? 'border-red-500' : 'border-gray-300'
              }`}
              placeholder="e.g., FinTech, SaaS, E-commerce, Healthcare"
            />
            {errors.industry && (
              <p className="mt-1 text-sm text-red-600">{errors.industry}</p>
            )}
          </div>

          {/* Geography */}
          <div>
            <label htmlFor="geography" className="block text-sm font-semibold text-gray-900 mb-2">
              Target Geography <span className="text-red-500">*</span>
            </label>
            <select
              id="geography"
              name="geography"
              required
              value={formData.geography}
              onChange={handleChange}
              className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-gray-900 focus:border-transparent text-gray-900 bg-white ${
                errors.geography ? 'border-red-500' : 'border-gray-300'
              }`}
            >
              <option value="">Select geography...</option>
              {GEOGRAPHY_OPTIONS.map(option => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
            {errors.geography && (
              <p className="mt-1 text-sm text-red-600">{errors.geography}</p>
            )}
            {formData.geography === 'Other' && (
              <input
                type="text"
                name="geography_other"
                placeholder="Specify geography..."
                className="mt-2 w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gray-900 focus:border-transparent text-gray-900"
                onChange={(e) => setFormData(prev => ({ ...prev, geography: e.target.value }))}
              />
            )}
          </div>

          {/* Customer Type */}
          <div>
            <label htmlFor="customer_type" className="block text-sm font-semibold text-gray-900 mb-2">
              Customer Type <span className="text-red-500">*</span>
            </label>
            <select
              id="customer_type"
              name="customer_type"
              required
              value={formData.customer_type}
              onChange={handleChange}
              className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-gray-900 focus:border-transparent text-gray-900 bg-white ${
                errors.customer_type ? 'border-red-500' : 'border-gray-300'
              }`}
            >
              <option value="">Select customer type...</option>
              {CUSTOMER_TYPE_OPTIONS.map(option => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
            {errors.customer_type && (
              <p className="mt-1 text-sm text-red-600">{errors.customer_type}</p>
            )}
          </div>

          {/* Business Model */}
          <div>
            <label htmlFor="business_model" className="block text-sm font-semibold text-gray-900 mb-2">
              Business Model <span className="text-red-500">*</span>
            </label>
            <select
              id="business_model"
              name="business_model"
              required
              value={formData.business_model}
              onChange={handleChange}
              className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-gray-900 focus:border-transparent text-gray-900 bg-white ${
                errors.business_model ? 'border-red-500' : 'border-gray-300'
              }`}
            >
              <option value="">Select business model...</option>
              {BUSINESS_MODEL_OPTIONS.map(option => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
            {errors.business_model && (
              <p className="mt-1 text-sm text-red-600">{errors.business_model}</p>
            )}
          </div>

          {/* Price Assumption */}
          <div>
            <label htmlFor="price_assumption" className="block text-sm font-semibold text-gray-900 mb-2">
              Price Assumption (Optional)
            </label>
            <input
              type="number"
              id="price_assumption"
              name="price_assumption"
              step="0.01"
              min="0"
              value={formData.price_assumption}
              onChange={handleChange}
              className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-gray-900 focus:border-transparent text-gray-900 ${
                errors.price_assumption ? 'border-red-500' : 'border-gray-300'
              }`}
              placeholder="e.g., 99.99 (monthly subscription price)"
            />
            {errors.price_assumption && (
              <p className="mt-1 text-sm text-red-600">{errors.price_assumption}</p>
            )}
            <p className="mt-1 text-xs text-gray-500">
              Average price point or subscription amount per customer
            </p>
          </div>

          {/* Notes */}
          <div>
            <label htmlFor="notes" className="block text-sm font-semibold text-gray-900 mb-2">
              Additional Notes (Optional)
            </label>
            <textarea
              id="notes"
              name="notes"
              rows={4}
              value={formData.notes}
              onChange={handleChange}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gray-900 focus:border-transparent resize-none text-gray-900"
              placeholder="Any additional context, constraints, or specific considerations..."
            />
          </div>

          {/* Submit Button */}
          <div className="pt-4">
            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-4 px-6 bg-gray-900 text-white font-semibold text-lg rounded-lg hover:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-gray-900 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isLoading ? 'Analyzing...' : 'Analyze Market Viability'}
            </button>
            <p className="mt-3 text-center text-sm text-gray-500">
              Analysis typically takes 30-60 seconds
            </p>
          </div>
        </form>
      </div>
    </div>
  )
}
