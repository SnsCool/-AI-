'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import Header from '@/components/Header'

interface NotionDoc {
  id: string
  title: string
  path: string
  hasTranscript: boolean
  hasPdfText: boolean
  hasLinkContent: boolean
  transcriptCount: number
  pdfTextCount: number
  linkContentCount: number
}

interface Stats {
  withTranscripts: number
  withPdfText: number
  withLinkContent: number
}

export default function NotionDocsPage() {
  const [docs, setDocs] = useState<NotionDoc[]>([])
  const [stats, setStats] = useState<Stats | null>(null)
  const [loading, setLoading] = useState(true)
  const [searchText, setSearchText] = useState('')
  const [filter, setFilter] = useState('')

  useEffect(() => {
    fetchDocs()
  }, [searchText, filter])

  const fetchDocs = async () => {
    try {
      const params = new URLSearchParams()
      if (searchText) params.set('search', searchText)
      if (filter) params.set('filter', filter)

      const res = await fetch(`/api/notion?${params}`)
      const data = await res.json()
      setDocs(data.docs || [])
      setStats(data.stats || null)
    } catch (error) {
      console.error('データ取得エラー:', error)
    } finally {
      setLoading(false)
    }
  }

  const filters = [
    { value: '', label: 'すべて' },
    { value: 'enriched', label: '追加コンテンツあり' },
    { value: 'transcript', label: '文字起こしあり' },
    { value: 'pdf', label: 'PDFテキストあり' },
    { value: 'link', label: 'リンクコンテンツあり' },
  ]

  return (
    <main className="min-h-screen bg-gray-50">
      <Header />
      <div className="max-w-6xl mx-auto px-4 py-6">
        {/* Stats */}
        {stats && (
          <div className="grid grid-cols-3 gap-4 mb-6">
            <div className="bg-white rounded-lg p-4 border border-gray-200">
              <div className="text-2xl font-bold text-purple-600">{stats.withTranscripts}</div>
              <div className="text-sm text-gray-500">文字起こし付き</div>
            </div>
            <div className="bg-white rounded-lg p-4 border border-gray-200">
              <div className="text-2xl font-bold text-blue-600">{stats.withPdfText}</div>
              <div className="text-sm text-gray-500">PDFテキスト付き</div>
            </div>
            <div className="bg-white rounded-lg p-4 border border-gray-200">
              <div className="text-2xl font-bold text-green-600">{stats.withLinkContent}</div>
              <div className="text-sm text-gray-500">リンクコンテンツ付き</div>
            </div>
          </div>
        )}

        {/* Search and Filter */}
        <div className="bg-white rounded-lg p-4 border border-gray-200 mb-6">
          <div className="flex gap-4 items-center">
            <input
              type="text"
              placeholder="ドキュメントを検索..."
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              className="flex-1 px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <select
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {filters.map(f => (
                <option key={f.value} value={f.value}>{f.label}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Document List */}
        {loading ? (
          <div className="text-center py-12 text-gray-500">読み込み中...</div>
        ) : docs.length === 0 ? (
          <div className="text-center py-12 text-gray-500">ドキュメントが見つかりません</div>
        ) : (
          <div className="space-y-2">
            <div className="text-sm text-gray-500 mb-4">{docs.length} 件のドキュメント</div>
            {docs.map(doc => (
              <Link
                key={doc.id}
                href={`/notion/${doc.id}`}
                className="block bg-white rounded-lg p-4 border border-gray-200 hover:border-blue-300 hover:shadow-sm transition-all"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h3 className="font-medium text-gray-800">{doc.title}</h3>
                    <p className="text-sm text-gray-500 mt-1">{doc.path}</p>
                  </div>
                  <div className="flex gap-2 ml-4">
                    {doc.hasTranscript && (
                      <span className="px-2 py-1 text-xs bg-purple-100 text-purple-700 rounded-full">
                        文字起こし {doc.transcriptCount}
                      </span>
                    )}
                    {doc.hasPdfText && (
                      <span className="px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded-full">
                        PDF {doc.pdfTextCount}
                      </span>
                    )}
                    {doc.hasLinkContent && (
                      <span className="px-2 py-1 text-xs bg-green-100 text-green-700 rounded-full">
                        リンク {doc.linkContentCount}
                      </span>
                    )}
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </main>
  )
}
