'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Header from '@/components/Header'

interface AssociatedContent {
  type: 'transcript' | 'pdf_text' | 'link_content'
  filename: string
  content: string
  title?: string
}

interface NotionDocDetail {
  id: string
  title: string
  path: string
  content: string
  associatedContent: AssociatedContent[]
  stats: {
    transcripts: number
    pdfTexts: number
    linkContents: number
  }
}

export default function NotionDocDetailPage() {
  const params = useParams()
  const router = useRouter()
  const [doc, setDoc] = useState<NotionDocDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<'main' | 'transcript' | 'pdf' | 'link'>('main')
  const [selectedContent, setSelectedContent] = useState<AssociatedContent | null>(null)

  useEffect(() => {
    fetchDoc()
  }, [params.id])

  const fetchDoc = async () => {
    try {
      const res = await fetch(`/api/notion/${params.id}`)
      const data = await res.json()
      setDoc(data.doc)

      // Auto-select first transcript if available
      if (data.doc?.associatedContent?.length > 0) {
        setSelectedContent(data.doc.associatedContent[0])
        const firstType = data.doc.associatedContent[0].type
        if (firstType === 'transcript') setActiveTab('transcript')
        else if (firstType === 'pdf_text') setActiveTab('pdf')
        else if (firstType === 'link_content') setActiveTab('link')
      }
    } catch (error) {
      console.error('データ取得エラー:', error)
    } finally {
      setLoading(false)
    }
  }

  const getContentByType = (type: string) => {
    return doc?.associatedContent.filter(c => c.type === type) || []
  }

  const getTabLabel = (type: string) => {
    switch (type) {
      case 'transcript': return '文字起こし'
      case 'pdf_text': return 'PDFテキスト'
      case 'link_content': return 'リンクコンテンツ'
      default: return type
    }
  }

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'transcript': return 'purple'
      case 'pdf_text': return 'blue'
      case 'link_content': return 'green'
      default: return 'gray'
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-gray-600">読み込み中...</div>
      </div>
    )
  }

  if (!doc) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-gray-600">ドキュメントが見つかりません</div>
      </div>
    )
  }

  const transcripts = getContentByType('transcript')
  const pdfTexts = getContentByType('pdf_text')
  const linkContents = getContentByType('link_content')

  return (
    <main className="min-h-screen bg-gray-50">
      <Header />
      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Back button and title */}
        <div className="mb-6">
          <button
            onClick={() => router.back()}
            className="flex items-center text-gray-600 hover:text-gray-800 mb-4"
          >
            <span className="mr-1">←</span> 戻る
          </button>
          <h2 className="text-2xl font-bold text-gray-800">{doc.title}</h2>
          <p className="text-sm text-gray-500 mt-1">{doc.path}</p>
        </div>

        {/* Stats badges */}
        <div className="flex gap-2 mb-6">
          {doc.stats.transcripts > 0 && (
            <span className="px-3 py-1 text-sm bg-purple-100 text-purple-700 rounded-full">
              文字起こし: {doc.stats.transcripts}件
            </span>
          )}
          {doc.stats.pdfTexts > 0 && (
            <span className="px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded-full">
              PDFテキスト: {doc.stats.pdfTexts}件
            </span>
          )}
          {doc.stats.linkContents > 0 && (
            <span className="px-3 py-1 text-sm bg-green-100 text-green-700 rounded-full">
              リンクコンテンツ: {doc.stats.linkContents}件
            </span>
          )}
        </div>

        {/* Content area */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Main document */}
          <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
            <div className="bg-gray-100 px-4 py-3 border-b border-gray-200">
              <h3 className="font-medium text-gray-700">メインドキュメント</h3>
            </div>
            <div className="p-4 max-h-[600px] overflow-y-auto">
              <div className="prose prose-sm max-w-none whitespace-pre-wrap text-gray-700">
                {doc.content}
              </div>
            </div>
          </div>

          {/* Associated content */}
          <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
            {/* Tabs */}
            <div className="bg-gray-100 px-4 py-2 border-b border-gray-200 flex gap-2 overflow-x-auto">
              {transcripts.length > 0 && (
                <button
                  onClick={() => {
                    setActiveTab('transcript')
                    setSelectedContent(transcripts[0])
                  }}
                  className={`px-3 py-1 text-sm rounded-md transition-colors ${
                    activeTab === 'transcript'
                      ? 'bg-purple-600 text-white'
                      : 'bg-white text-gray-600 hover:bg-purple-100'
                  }`}
                >
                  文字起こし ({transcripts.length})
                </button>
              )}
              {pdfTexts.length > 0 && (
                <button
                  onClick={() => {
                    setActiveTab('pdf')
                    setSelectedContent(pdfTexts[0])
                  }}
                  className={`px-3 py-1 text-sm rounded-md transition-colors ${
                    activeTab === 'pdf'
                      ? 'bg-blue-600 text-white'
                      : 'bg-white text-gray-600 hover:bg-blue-100'
                  }`}
                >
                  PDF ({pdfTexts.length})
                </button>
              )}
              {linkContents.length > 0 && (
                <button
                  onClick={() => {
                    setActiveTab('link')
                    setSelectedContent(linkContents[0])
                  }}
                  className={`px-3 py-1 text-sm rounded-md transition-colors ${
                    activeTab === 'link'
                      ? 'bg-green-600 text-white'
                      : 'bg-white text-gray-600 hover:bg-green-100'
                  }`}
                >
                  リンク ({linkContents.length})
                </button>
              )}
              {doc.associatedContent.length === 0 && (
                <span className="text-sm text-gray-500 py-1">追加コンテンツなし</span>
              )}
            </div>

            {/* Content selector (if multiple items) */}
            {activeTab === 'transcript' && transcripts.length > 1 && (
              <div className="px-4 py-2 border-b border-gray-200 bg-gray-50">
                <select
                  value={selectedContent?.filename || ''}
                  onChange={(e) => {
                    const content = transcripts.find(c => c.filename === e.target.value)
                    if (content) setSelectedContent(content)
                  }}
                  className="w-full px-3 py-1 text-sm border border-gray-300 rounded-md"
                >
                  {transcripts.map(c => (
                    <option key={c.filename} value={c.filename}>
                      {c.title || c.filename}
                    </option>
                  ))}
                </select>
              </div>
            )}
            {activeTab === 'pdf' && pdfTexts.length > 1 && (
              <div className="px-4 py-2 border-b border-gray-200 bg-gray-50">
                <select
                  value={selectedContent?.filename || ''}
                  onChange={(e) => {
                    const content = pdfTexts.find(c => c.filename === e.target.value)
                    if (content) setSelectedContent(content)
                  }}
                  className="w-full px-3 py-1 text-sm border border-gray-300 rounded-md"
                >
                  {pdfTexts.map(c => (
                    <option key={c.filename} value={c.filename}>
                      {c.title || c.filename}
                    </option>
                  ))}
                </select>
              </div>
            )}
            {activeTab === 'link' && linkContents.length > 1 && (
              <div className="px-4 py-2 border-b border-gray-200 bg-gray-50">
                <select
                  value={selectedContent?.filename || ''}
                  onChange={(e) => {
                    const content = linkContents.find(c => c.filename === e.target.value)
                    if (content) setSelectedContent(content)
                  }}
                  className="w-full px-3 py-1 text-sm border border-gray-300 rounded-md"
                >
                  {linkContents.map(c => (
                    <option key={c.filename} value={c.filename}>
                      {c.title || c.filename}
                    </option>
                  ))}
                </select>
              </div>
            )}

            {/* Selected content */}
            <div className="p-4 max-h-[600px] overflow-y-auto">
              {selectedContent ? (
                <div>
                  {selectedContent.title && (
                    <h4 className="font-medium text-gray-800 mb-3">{selectedContent.title}</h4>
                  )}
                  <div className="prose prose-sm max-w-none whitespace-pre-wrap text-gray-700 font-mono text-xs leading-relaxed">
                    {selectedContent.content}
                  </div>
                </div>
              ) : (
                <div className="text-gray-500 text-center py-8">
                  追加コンテンツはありません
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </main>
  )
}
