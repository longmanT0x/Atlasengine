'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'

interface AnalyzeResponse {
  verdict: 'GO' | 'NO-GO' | 'CONDITIONAL'
  confidence_score: number
  executive_summary: string[]
  market: {
    tam: { min: number; base: number; max: number; method?: string; assumptions: string[] }
    sam: { min: number; base: number; max: number; assumptions: string[] }
    som: { min: number; base: number; max: number; assumptions: string[] }
  }
  competitors: Array<{
    name: string
    positioning: string
    pricing: string
    geography: string
    differentiator: string
    source_url: string
  }>
  risks: {
    market: string[]
    competition: string[]
    regulatory: string[]
    distribution: string[]
  }
  assumptions: string[]
  disconfirming_evidence: string[]
  sources: Array<{
    title: string
    url: string
    excerpt: string
  }>
  key_unknowns: string[]
  next_7_days_tests: Array<{
    test: string
    method: string
    success_threshold: string
  }>
  scenarios: {
    bear?: { name: string; market: any }
    base?: { name: string; market: any }
    bull?: { name: string; market: any }
  }
  sensitivity_analysis: Array<{
    assumption_name: string
    base_som: number
    impact_minus_30pct: number
    impact_plus_30pct: number
    impact_magnitude: number
  }>
  evidence_ledger?: Array<{
    id: string
    claim_text: string
    claim_type: string
    value?: number
    unit?: string
    source_url: string
    excerpt: string
    retrieved_at: string
    credibility_score: string
    claim_confidence: string
  }>
}

export default function ReportPage() {
  const router = useRouter()
  const [data, setData] = useState<AnalyzeResponse | null>(null)
  const [requestData, setRequestData] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isDownloading, setIsDownloading] = useState(false)
  const [pdfAvailable, setPdfAvailable] = useState(true)
  const [pdfError, setPdfError] = useState<string | null>(null)
  const [debugMode, setDebugMode] = useState(false)
  const [showRawJson, setShowRawJson] = useState(false)
  const [copiedSummary, setCopiedSummary] = useState(false)

  useEffect(() => {
    const runAnalysis = async () => {
      try {
        // Get request data from localStorage
        const requestDataStr = localStorage.getItem('atlas_request')
        if (!requestDataStr) {
          router.push('/')
          return
        }

        const parsedRequest = JSON.parse(requestDataStr)
        setRequestData(parsedRequest)
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

        // Make API call
        const response = await fetch(`${apiUrl}/analyze`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            ...parsedRequest,
            price_assumption: parsedRequest.price_assumption ? parseFloat(parsedRequest.price_assumption) : null,
          }),
        })

        if (!response.ok) {
          throw new Error(`Analysis failed: ${response.statusText}`)
        }

        const result = await response.json()
        setData(result)
        setDebugMode(parsedRequest.debug || false)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to analyze market viability')
      } finally {
        setIsLoading(false)
      }
    }

    // Check if PDF endpoint is available
    const checkPdfEndpoint = async () => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'
        // Try a HEAD request to check if endpoint exists (some servers don't support HEAD, so we'll catch and continue)
        const response = await fetch(`${apiUrl}/export/pdf`, {
          method: 'HEAD',
        })
        if (response.status === 404 || response.status === 405) {
          setPdfAvailable(false)
          setPdfError('PDF export endpoint not available')
        }
      } catch (err) {
        // If HEAD fails, we'll still show the button and let the user try
        // The actual POST request will handle the error
      }
    }

    runAnalysis()
    checkPdfEndpoint()
  }, [router])

  const handleDownloadPDF = async () => {
    setIsDownloading(true)
    setPdfError(null)
    
    try {
      const requestDataStr = localStorage.getItem('atlas_request')
      if (!requestDataStr) {
        setPdfError('Request data not found')
        setPdfAvailable(false)
        return
      }

      const requestData = JSON.parse(requestDataStr)
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

      const response = await fetch(`${apiUrl}/export/pdf`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ...requestData,
          price_assumption: requestData.price_assumption ? parseFloat(requestData.price_assumption) : null,
        }),
      })

      if (response.status === 404) {
        setPdfError('PDF export endpoint not available')
        setPdfAvailable(false)
        return
      }

      if (!response.ok) {
        throw new Error(`PDF generation failed: ${response.statusText}`)
      }

      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'atlas_memo.pdf'
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to download PDF'
      setPdfError(errorMessage)
      setPdfAvailable(false)
    } finally {
      setIsDownloading(false)
    }
  }

  const handleEditInputs = () => {
    router.push('/')
  }

  const handleCopySummary = async () => {
    if (!data) return
    const summaryText = data.executive_summary.join('\n')
    try {
      await navigator.clipboard.writeText(summaryText)
      setCopiedSummary(true)
      setTimeout(() => setCopiedSummary(false), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  const handleExportJSON = () => {
    if (!data) return
    const jsonStr = JSON.stringify(data, null, 2)
    const blob = new Blob([jsonStr], { type: 'application/json' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `atlas_analysis_${new Date().toISOString().split('T')[0]}.json`
    document.body.appendChild(a)
    a.click()
    window.URL.revokeObjectURL(url)
    document.body.removeChild(a)
  }

  const formatCurrency = (value: number) => {
    if (value >= 1_000_000_000) {
      return `$${(value / 1_000_000_000).toFixed(2)}B`
    } else if (value >= 1_000_000) {
      return `$${(value / 1_000_000).toFixed(2)}M`
    } else {
      return `$${value.toLocaleString()}`
    }
  }

  const getVerdictColor = (verdict: string) => {
    switch (verdict) {
      case 'GO':
        return 'bg-green-100 text-green-800 border-green-300'
      case 'NO-GO':
        return 'bg-red-100 text-red-800 border-red-300'
      case 'CONDITIONAL':
        return 'bg-orange-100 text-orange-800 border-orange-300'
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300'
    }
  }

  // Loading State
  if (isLoading) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 mx-auto mb-4"></div>
          <p className="text-lg font-medium text-gray-600">Analyzing market viability...</p>
          <p className="text-sm text-gray-500 mt-2">This may take 30-60 seconds</p>
        </div>
      </div>
    )
  }

  // Error State
  if (error || !data) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="text-center max-w-md px-6">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">Analysis Failed</h1>
          <p className="text-gray-600 mb-6">{error || 'Unknown error occurred'}</p>
          <div className="flex gap-3 justify-center">
            <button
              onClick={() => router.push('/')}
              className="px-6 py-3 bg-gray-900 text-white font-semibold rounded-lg hover:bg-gray-800"
            >
              Start Over
            </button>
            <button
              onClick={handleEditInputs}
              className="px-6 py-3 border border-gray-300 text-gray-700 font-semibold rounded-lg hover:bg-gray-50"
            >
              Edit Inputs
            </button>
          </div>
        </div>
      </div>
    )
  }

  // Success State - Memo Layout
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
        {/* Header */}
        <div className="mb-8">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
            <div>
              <h1 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-2">ATLAS MEMO</h1>
              <p className="text-sm text-gray-600">{new Date().toLocaleDateString('en-US', { 
                year: 'numeric', 
                month: 'long', 
                day: 'numeric' 
              })}</p>
            </div>
            <div className="flex flex-wrap gap-2 sm:gap-3 items-center">
              {pdfAvailable && (
                <button
                  onClick={handleDownloadPDF}
                  disabled={isDownloading}
                  aria-label="Download PDF memo"
                  className="px-4 py-2 bg-gray-900 text-white rounded-lg text-sm font-medium hover:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-gray-900 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {isDownloading ? 'Downloading...' : 'Download PDF'}
                </button>
              )}
              <button
                onClick={handleExportJSON}
                aria-label="Export JSON data"
                className="px-4 py-2 bg-white border border-gray-300 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-900 focus:ring-offset-2 transition-colors"
              >
                Export JSON
              </button>
              {pdfError && !pdfAvailable && (
                <div className="px-4 py-2 text-xs text-gray-500 bg-gray-50 rounded-lg border border-gray-200" role="status">
                  PDF unavailable
                </div>
              )}
              <div className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg bg-white">
                <input
                  type="checkbox"
                  id="debug-mode"
                  checked={debugMode}
                  onChange={(e) => setDebugMode(e.target.checked)}
                  aria-label="Enable debug mode"
                  className="w-4 h-4 text-gray-900 border-gray-300 rounded focus:ring-2 focus:ring-gray-900 focus:ring-offset-2"
                />
                <label htmlFor="debug-mode" className="text-sm font-medium text-gray-700 cursor-pointer">
                  Debug Mode
                </label>
              </div>
            </div>
          </div>

          {/* Idea Title */}
          {requestData?.idea && (
            <div className="mb-6 p-5 bg-white rounded-xl border border-gray-200 shadow-sm">
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Idea</p>
              <p className="text-lg text-gray-900 leading-relaxed">{requestData.idea}</p>
            </div>
          )}

          {/* Verdict Badge and Confidence */}
          <div className="flex flex-wrap items-center gap-6 mb-8">
            <div>
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Verdict</p>
              <span className={`inline-block px-5 py-2.5 rounded-lg border-2 font-bold text-lg ${getVerdictColor(data.verdict)}`} role="status" aria-label={`Verdict: ${data.verdict}`}>
                {data.verdict}
              </span>
            </div>
            <div>
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Confidence</p>
              <p className="text-2xl font-bold text-gray-900" aria-label={`Confidence score: ${data.confidence_score} out of 100`}>{data.confidence_score}/100</p>
            </div>
          </div>
        </div>

        {/* Executive Summary */}
        <section className="mb-8">
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-2xl font-bold text-gray-900">Executive Summary</h2>
              <button
                onClick={handleCopySummary}
                aria-label="Copy executive summary to clipboard"
                className="px-3 py-1.5 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-900 focus:ring-offset-2 transition-colors"
              >
                {copiedSummary ? '✓ Copied' : 'Copy'}
              </button>
            </div>
            <ul className="space-y-3" role="list">
              {data.executive_summary.map((item, idx) => (
                <li key={idx} className="flex items-start">
                  <span className="text-gray-400 mr-3 mt-1.5 flex-shrink-0" aria-hidden="true">•</span>
                  <span className="text-gray-700 leading-relaxed">{item}</span>
                </li>
              ))}
            </ul>
          </div>
        </section>

        {/* Market Cards: TAM / SAM / SOM */}
        <section className="mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Market Analysis</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 sm:gap-6">
            {/* TAM Card */}
            <div className="p-6 bg-white border border-gray-200 rounded-xl shadow-sm">
              <h3 className="text-lg font-bold text-gray-900 mb-4">TAM</h3>
              <div className="space-y-2 mb-4">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Min:</span>
                  <span className="font-semibold text-gray-900">{formatCurrency(data.market.tam.min)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Base:</span>
                  <span className="font-bold text-lg text-gray-900">{formatCurrency(data.market.tam.base)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Max:</span>
                  <span className="font-semibold text-gray-900">{formatCurrency(data.market.tam.max)}</span>
                </div>
              </div>
              {data.market.tam.method && (
                <p className="text-xs text-gray-500 mt-4 pt-4 border-t border-gray-200">
                  Method: {data.market.tam.method}
                </p>
              )}
            </div>

            {/* SAM Card */}
            <div className="p-6 bg-white border border-gray-200 rounded-xl shadow-sm">
              <h3 className="text-lg font-bold text-gray-900 mb-4">SAM</h3>
              <div className="space-y-2 mb-4">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Min:</span>
                  <span className="font-semibold text-gray-900">{formatCurrency(data.market.sam.min)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Base:</span>
                  <span className="font-bold text-lg text-gray-900">{formatCurrency(data.market.sam.base)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Max:</span>
                  <span className="font-semibold text-gray-900">{formatCurrency(data.market.sam.max)}</span>
                </div>
              </div>
            </div>

            {/* SOM Card */}
            <div className="p-6 bg-white border border-gray-200 rounded-xl shadow-sm">
              <h3 className="text-lg font-bold text-gray-900 mb-4">SOM</h3>
              <div className="space-y-2 mb-4">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Min:</span>
                  <span className="font-semibold text-gray-900">{formatCurrency(data.market.som.min)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Base:</span>
                  <span className="font-bold text-lg text-gray-900">{formatCurrency(data.market.som.base)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Max:</span>
                  <span className="font-semibold text-gray-900">{formatCurrency(data.market.som.max)}</span>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Scenarios Table */}
        {data.scenarios && (data.scenarios.bear || data.scenarios.base || data.scenarios.bull) && (
          <section className="mb-8">
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">Scenarios</h2>
              <div className="overflow-x-auto -mx-6 px-6">
                <table className="w-full border-collapse min-w-[500px]">
                  <thead>
                    <tr className="bg-gray-900 text-white">
                      <th className="px-4 py-3 text-left font-semibold text-sm">Scenario</th>
                      <th className="px-4 py-3 text-right font-semibold text-sm">TAM</th>
                      <th className="px-4 py-3 text-right font-semibold text-sm">SAM</th>
                      <th className="px-4 py-3 text-right font-semibold text-sm">SOM</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.scenarios.bear && (
                      <tr className="border-b border-gray-200 hover:bg-gray-50 transition-colors">
                        <td className="px-4 py-3 font-medium text-gray-900">Bear</td>
                        <td className="px-4 py-3 text-right text-gray-700">{formatCurrency(data.scenarios.bear.market.tam.base)}</td>
                        <td className="px-4 py-3 text-right text-gray-700">{formatCurrency(data.scenarios.bear.market.sam.base)}</td>
                        <td className="px-4 py-3 text-right text-gray-700">{formatCurrency(data.scenarios.bear.market.som.base)}</td>
                      </tr>
                    )}
                    {data.scenarios.base && (
                      <tr className="border-b border-gray-200 bg-gray-50 hover:bg-gray-100 transition-colors">
                        <td className="px-4 py-3 font-medium text-gray-900">Base</td>
                        <td className="px-4 py-3 text-right text-gray-900 font-semibold">{formatCurrency(data.scenarios.base.market.tam.base)}</td>
                        <td className="px-4 py-3 text-right text-gray-900 font-semibold">{formatCurrency(data.scenarios.base.market.sam.base)}</td>
                        <td className="px-4 py-3 text-right text-gray-900 font-semibold">{formatCurrency(data.scenarios.base.market.som.base)}</td>
                      </tr>
                    )}
                    {data.scenarios.bull && (
                      <tr className="border-b border-gray-200 hover:bg-gray-50 transition-colors">
                        <td className="px-4 py-3 font-medium text-gray-900">Bull</td>
                        <td className="px-4 py-3 text-right text-gray-700">{formatCurrency(data.scenarios.bull.market.tam.base)}</td>
                        <td className="px-4 py-3 text-right text-gray-700">{formatCurrency(data.scenarios.bull.market.sam.base)}</td>
                        <td className="px-4 py-3 text-right text-gray-700">{formatCurrency(data.scenarios.bull.market.som.base)}</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </section>
        )}

        {/* Competitors Table */}
        {data.competitors && data.competitors.length > 0 && (
          <section className="mb-8">
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">Competitors</h2>
              <div className="overflow-x-auto -mx-6 px-6">
                <table className="w-full border-collapse min-w-[800px]">
                  <thead>
                    <tr className="bg-gray-900 text-white">
                      <th className="px-4 py-3 text-left font-semibold text-sm">Name</th>
                      <th className="px-4 py-3 text-left font-semibold text-sm">Positioning</th>
                      <th className="px-4 py-3 text-left font-semibold text-sm">Pricing</th>
                      <th className="px-4 py-3 text-left font-semibold text-sm">Geography</th>
                      <th className="px-4 py-3 text-left font-semibold text-sm">Differentiator</th>
                      <th className="px-4 py-3 text-left font-semibold text-sm">Source</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.competitors.map((comp, idx) => (
                      <tr key={idx} className={`border-b border-gray-200 ${idx % 2 === 0 ? 'bg-white' : 'bg-gray-50'} hover:bg-gray-100 transition-colors`}>
                        <td className="px-4 py-3 font-medium text-gray-900">{comp.name}</td>
                        <td className="px-4 py-3 text-gray-700 text-sm">{comp.positioning}</td>
                        <td className="px-4 py-3 text-gray-700 text-sm">{comp.pricing}</td>
                        <td className="px-4 py-3 text-gray-700 text-sm">{comp.geography}</td>
                        <td className="px-4 py-3 text-gray-700 text-sm">{comp.differentiator}</td>
                        <td className="px-4 py-3">
                          <a 
                            href={comp.source_url} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            aria-label={`View source for ${comp.name}`}
                            className="text-blue-600 hover:text-blue-800 hover:underline text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 rounded"
                          >
                            Link
                          </a>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </section>
        )}

        {/* Risks Section */}
        <section className="mb-8">
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Risks</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {data.risks.market.length > 0 && (
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-3">Market Risks</h3>
                <ul className="space-y-3" role="list">
                  {data.risks.market.map((risk, idx) => (
                    <li key={idx} className="text-gray-700 flex items-start">
                      <span className="text-gray-400 mr-3 mt-1.5 flex-shrink-0" aria-hidden="true">•</span>
                      <span className="leading-relaxed">{risk}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {data.risks.competition.length > 0 && (
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-3">Competition Risks</h3>
                <ul className="space-y-3" role="list">
                  {data.risks.competition.map((risk, idx) => (
                    <li key={idx} className="text-gray-700 flex items-start">
                      <span className="text-gray-400 mr-3 mt-1.5 flex-shrink-0" aria-hidden="true">•</span>
                      <span className="leading-relaxed">{risk}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {data.risks.regulatory.length > 0 && (
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-3">Regulatory Risks</h3>
                <ul className="space-y-3" role="list">
                  {data.risks.regulatory.map((risk, idx) => (
                    <li key={idx} className="text-gray-700 flex items-start">
                      <span className="text-gray-400 mr-3 mt-1.5 flex-shrink-0" aria-hidden="true">•</span>
                      <span className="leading-relaxed">{risk}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {data.risks.distribution.length > 0 && (
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-3">Distribution Risks</h3>
                <ul className="space-y-3" role="list">
                  {data.risks.distribution.map((risk, idx) => (
                    <li key={idx} className="text-gray-700 flex items-start">
                      <span className="text-gray-400 mr-3 mt-1.5 flex-shrink-0" aria-hidden="true">•</span>
                      <span className="leading-relaxed">{risk}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
          </div>
        </section>

        {/* Assumptions */}
        {data.assumptions && data.assumptions.length > 0 && (
          <section className="mb-8">
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">Assumptions</h2>
              <ul className="space-y-3" role="list">
                {data.assumptions.map((assumption, idx) => (
                  <li key={idx} className="text-gray-700 flex items-start">
                    <span className="text-gray-400 mr-3 mt-1.5 flex-shrink-0" aria-hidden="true">•</span>
                    <span className="leading-relaxed">{assumption}</span>
                  </li>
                ))}
              </ul>
            </div>
          </section>
        )}

        {/* Disconfirming Evidence */}
        {data.disconfirming_evidence && data.disconfirming_evidence.length > 0 && (
          <section className="mb-8">
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">Disconfirming Evidence</h2>
              <ul className="space-y-3" role="list">
                {data.disconfirming_evidence.map((evidence, idx) => (
                  <li key={idx} className="text-gray-700 flex items-start">
                    <span className="text-gray-400 mr-3 mt-1.5 flex-shrink-0" aria-hidden="true">•</span>
                    <span className="leading-relaxed">{evidence}</span>
                  </li>
                ))}
              </ul>
            </div>
          </section>
        )}

        {/* Sources List */}
        <section className="mb-8">
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Sources</h2>
            <div className="space-y-4">
            {data.sources.map((source, idx) => {
              // Try to get credibility from evidence ledger if available
              const sourceClaim = data.evidence_ledger?.find(
                (claim: any) => claim.source_url === source.url && claim.claim_type === 'source'
              )
              const credibility = sourceClaim?.credibility_score
              
              return (
                <div key={idx} className="p-4 bg-gray-50 rounded-lg border border-gray-200 hover:border-gray-300 transition-colors">
                  <div className="flex items-start justify-between mb-2">
                    <h3 className="font-semibold text-gray-900">{idx + 1}. {source.title}</h3>
                    {debugMode && credibility && (
                      <span className={`px-2 py-1 rounded text-xs font-medium ${
                        credibility === 'high' ? 'bg-green-100 text-green-800' :
                        credibility === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-red-100 text-red-800'
                      }`} aria-label={`Credibility: ${credibility}`}>
                        {credibility}
                      </span>
                    )}
                  </div>
                  {source.excerpt && (
                    <p className="text-sm text-gray-600 mb-2 leading-relaxed">{source.excerpt}</p>
                  )}
                  <a 
                    href={source.url} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    aria-label={`View source: ${source.title}`}
                    className="text-sm text-blue-600 hover:text-blue-800 hover:underline focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 rounded"
                  >
                    {source.url}
                  </a>
                </div>
              )
            })}
          </div>
          </div>
        </section>

        {/* Key Unknowns */}
        {data.key_unknowns && data.key_unknowns.length > 0 && (
          <section className="mb-8">
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">Key Unknowns</h2>
              <ul className="space-y-3" role="list">
                {data.key_unknowns.map((unknown, idx) => (
                  <li key={idx} className="text-gray-700 flex items-start">
                    <span className="text-gray-400 mr-3 mt-1.5 flex-shrink-0" aria-hidden="true">•</span>
                    <span className="leading-relaxed">{unknown}</span>
                  </li>
                ))}
              </ul>
            </div>
          </section>
        )}

        {/* Next 7 Days Tests */}
        {data.next_7_days_tests && data.next_7_days_tests.length > 0 && (
          <section className="mb-8">
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">Next 7 Days Tests</h2>
              <div className="space-y-4">
                {data.next_7_days_tests.map((test, idx) => (
                  <div key={idx} className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                    <h3 className="font-semibold text-gray-900 mb-2">{test.test}</h3>
                    <div className="space-y-1 text-sm text-gray-600">
                      <p><span className="font-medium">Method:</span> {test.method}</p>
                      <p><span className="font-medium">Success Threshold:</span> {test.success_threshold}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </section>
        )}

        {/* Debug Mode Sections */}
        {debugMode && (
          <>
            {/* Raw JSON Response */}
            <section className="mb-8">
              <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-2xl font-bold text-gray-900">Raw JSON Response</h2>
                  <button
                    onClick={() => setShowRawJson(!showRawJson)}
                    aria-label={showRawJson ? 'Collapse JSON' : 'Expand JSON'}
                    className="px-3 py-1.5 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-900 focus:ring-offset-2 transition-colors"
                  >
                    {showRawJson ? 'Collapse' : 'Expand'}
                  </button>
                </div>
                {showRawJson && (
                  <div className="p-4 bg-gray-900 rounded-lg overflow-auto">
                    <pre className="text-xs text-green-400 font-mono" aria-label="Raw JSON response">
                      {JSON.stringify(data, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            </section>

            {/* Evidence Ledger */}
            {data.evidence_ledger && data.evidence_ledger.length > 0 && (
              <section className="mb-8">
                <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
                  <h2 className="text-2xl font-bold text-gray-900 mb-6">Evidence Ledger</h2>
                  <div className="space-y-4">
                    {data.evidence_ledger.map((claim, idx) => (
                      <div key={idx} className="p-4 bg-gray-50 rounded-lg border border-gray-200 hover:border-gray-300 transition-colors">
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex-1">
                          <h3 className="font-semibold text-gray-900">{claim.claim_text}</h3>
                          <p className="text-sm text-gray-600 mt-1">
                            Type: <span className="font-medium">{claim.claim_type}</span>
                            {claim.claim_confidence && (
                              <> • Confidence: <span className="font-medium">{claim.claim_confidence}</span></>
                            )}
                          </p>
                        </div>
                        <div className="text-right ml-4">
                          <span className={`px-2 py-1 rounded text-xs font-medium ${
                            claim.credibility_score === 'high' ? 'bg-green-100 text-green-800' :
                            claim.credibility_score === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                            'bg-red-100 text-red-800'
                          }`}>
                            {claim.credibility_score}
                          </span>
                        </div>
                      </div>
                      {claim.value !== null && claim.value !== undefined && (
                        <p className="text-sm text-gray-700 mb-1">
                          <span className="font-medium">Value:</span> {claim.value} {claim.unit || ''}
                        </p>
                      )}
                      <p className="text-sm text-gray-600 mb-2">
                        <span className="font-medium">Excerpt:</span> {claim.excerpt}
                      </p>
                      <div className="flex items-center justify-between">
                        <a 
                          href={claim.source_url} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="text-xs text-blue-600 hover:underline"
                        >
                          {claim.source_url}
                        </a>
                        {claim.retrieved_at && (
                          <span className="text-xs text-gray-500">
                            {new Date(claim.retrieved_at).toLocaleString()}
                          </span>
                        )}
                      </div>
                    </div>
                    ))}
                  </div>
                </div>
              </section>
            )}
          </>
        )}

        {/* Action Buttons */}
        <div className="mt-12 pt-8 border-t border-gray-200 flex flex-wrap gap-4">
          <button
            onClick={() => router.push('/')}
            aria-label="Go back to home page"
            className="px-6 py-3 border border-gray-300 rounded-lg text-gray-700 font-medium hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-900 focus:ring-offset-2 transition-colors"
          >
            ← Back
          </button>
          <button
            onClick={handleEditInputs}
            aria-label="Edit analysis inputs"
            className="px-6 py-3 bg-gray-900 text-white rounded-lg font-medium hover:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-gray-900 focus:ring-offset-2 transition-colors"
          >
            Edit Inputs
          </button>
        </div>
      </div>
    </div>
  )
}
