'use client'

import { useState, useEffect, useMemo } from 'react'
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

// カテゴリ定義（Notionの構造に合わせる）
const CATEGORIES: { name: string; icon: string; color: string; items: string[] }[] = [
  {
    name: 'Levela全体',
    icon: '🏢',
    color: 'bg-amber-50 border-amber-200',
    items: ['全体会議議事録', 'Levelaメンバー紹介', 'LevelaのMVV', 'Levelaオンライン図書館'],
  },
  {
    name: '部署',
    icon: '🏛️',
    color: 'bg-stone-50 border-stone-200',
    items: [
      'CS部', 'マーケティング部', '工事中🚧マーケティング部', '営業ポータル',
      '社長室ポータル', 'クリエイティ部', '知足ポータル',
      'TikTok Shopマネタイズ講座ローンチ', 'AI Brain 知識ベース',
    ],
  },
  {
    name: '事業',
    icon: '💼',
    color: 'bg-orange-50 border-orange-200',
    items: [
      '新規事業_Monthly会議', '運用代行', 'AI教育事業', 'Mrs.PROTEIN',
      'ダイエット事業', 'アイレポート', '営業代行事業', 'コーチングスクール事業',
      'TikTokライブスクール', '各事業計画', 'UGC',
    ],
  },
  {
    name: 'マニュアル',
    icon: '💜',
    color: 'bg-purple-50 border-purple-200',
    items: [
      '採用決定後のフロー (New)', '業務対応マニュアル', 'ナレッジ共有',
      '週次_月次入力フォーマット', 'SnsClub講師紹介制度について',
    ],
  },
  {
    name: 'インテリジェンス',
    icon: '🧠',
    color: 'bg-teal-50 border-teal-200',
    items: ['教材格納庫', 'AIスクール用動画', 'AI活用事例ナレッジDB', '開発ツール'],
  },
  {
    name: 'その他',
    icon: '📦',
    color: 'bg-gray-50 border-gray-200',
    items: ['クライアントワークの報酬設定', 'カウンセリングメンバー募集', 'unnamed'],
  },
]

// ドキュメントアイテムコンポーネント
function DocItem({ doc, isTopLevel = false }: { doc: NotionDoc; isTopLevel?: boolean }) {
  const hasEnrichedContent = doc.hasTranscript || doc.hasPdfText || doc.hasLinkContent

  return (
    <Link
      href={`/notion/${doc.id}`}
      className={`flex items-center gap-2 py-1.5 px-2 rounded hover:bg-white/50 transition-colors ${
        isTopLevel ? '' : 'ml-2'
      }`}
    >
      <span className="text-sm">📄</span>
      <span className="text-sm text-gray-700 hover:text-blue-600 truncate flex-1">
        {doc.title}
      </span>
      {hasEnrichedContent && (
        <div className="flex gap-0.5">
          {doc.hasTranscript && <span className="text-xs">🎬</span>}
          {doc.hasPdfText && <span className="text-xs">📑</span>}
          {doc.hasLinkContent && <span className="text-xs">🔗</span>}
        </div>
      )}
    </Link>
  )
}

// ツリーアイテムコンポーネント（サブフォルダ用）
function TreeItem({ title, docs, level = 0 }: { title: string; docs: NotionDoc[]; level?: number }) {
  const [isOpen, setIsOpen] = useState(false)

  // このタイトルに直接対応するドキュメント
  const directDoc = docs.find(d => d.path === title || d.title === title)
  // 子ドキュメント
  const childDocs = docs.filter(d => {
    const parts = d.path.split('/')
    return parts[0] === title && parts.length > 1
  })

  // 子フォルダをグループ化
  const childFolders = new Map<string, NotionDoc[]>()
  childDocs.forEach(doc => {
    const parts = doc.path.split('/')
    if (parts.length > 1) {
      const childFolder = parts[1]
      if (!childFolders.has(childFolder)) {
        childFolders.set(childFolder, [])
      }
      childFolders.get(childFolder)!.push({
        ...doc,
        path: parts.slice(1).join('/'),
      })
    }
  })

  const hasChildren = childFolders.size > 0

  return (
    <div>
      <div
        className={`flex items-center gap-2 py-1.5 px-2 rounded cursor-pointer hover:bg-white/50 ${
          level === 0 ? '' : 'ml-' + (level * 2)
        }`}
        onClick={() => hasChildren && setIsOpen(!isOpen)}
      >
        {hasChildren ? (
          <span className="text-xs text-gray-400 w-3">{isOpen ? '▼' : '▶'}</span>
        ) : (
          <span className="w-3" />
        )}
        <span className="text-sm">{hasChildren ? (isOpen ? '📂' : '📁') : '📄'}</span>
        {directDoc ? (
          <Link
            href={`/notion/${directDoc.id}`}
            className="text-sm text-gray-700 hover:text-blue-600 truncate flex-1"
            onClick={(e) => e.stopPropagation()}
          >
            {title}
          </Link>
        ) : (
          <span className="text-sm text-gray-700 truncate flex-1">{title}</span>
        )}
      </div>
      {isOpen && hasChildren && (
        <div className="ml-4 border-l border-gray-200 pl-2">
          {Array.from(childFolders.entries()).map(([folder, folderDocs]) => (
            <TreeItem key={folder} title={folder} docs={folderDocs} level={level + 1} />
          ))}
        </div>
      )}
    </div>
  )
}

// カテゴリカードコンポーネント
function CategoryCard({
  category,
  docs,
}: {
  category: typeof CATEGORIES[0]
  docs: NotionDoc[]
}) {
  // このカテゴリに属するドキュメントをフィルタ
  const categoryDocs = docs.filter(doc => {
    const topFolder = doc.path.split('/')[0]
    return category.items.includes(topFolder)
  })

  // トップレベルフォルダごとにグループ化
  const folderGroups = new Map<string, NotionDoc[]>()
  category.items.forEach(item => {
    const itemDocs = categoryDocs.filter(d => d.path.split('/')[0] === item)
    if (itemDocs.length > 0) {
      folderGroups.set(item, itemDocs)
    }
  })

  return (
    <div className={`rounded-lg border-2 ${category.color} overflow-hidden`}>
      <div className="px-4 py-3 border-b border-inherit bg-white/50">
        <h3 className="font-medium text-gray-800 flex items-center gap-2">
          <span>{category.icon}</span>
          {category.name}
          <span className="text-xs text-gray-400 font-normal">({categoryDocs.length})</span>
        </h3>
      </div>
      <div className="p-3 max-h-80 overflow-y-auto">
        {folderGroups.size === 0 ? (
          <p className="text-sm text-gray-400 text-center py-4">該当なし</p>
        ) : (
          <div className="space-y-1">
            {Array.from(folderGroups.entries()).map(([folder, folderDocs]) => (
              <TreeItem key={folder} title={folder} docs={folderDocs} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default function NotionDocsPage() {
  const [docs, setDocs] = useState<NotionDoc[]>([])
  const [stats, setStats] = useState<Stats | null>(null)
  const [loading, setLoading] = useState(true)
  const [searchText, setSearchText] = useState('')
  const [filter, setFilter] = useState('')
  const [viewMode, setViewMode] = useState<'category' | 'tree'>('category')

  useEffect(() => {
    fetchDocs()
  }, [filter])

  const fetchDocs = async () => {
    try {
      const params = new URLSearchParams()
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

  // 検索フィルター適用
  const filteredDocs = useMemo(() => {
    if (!searchText) return docs
    const searchLower = searchText.toLowerCase()
    return docs.filter(doc =>
      doc.title.toLowerCase().includes(searchLower) ||
      doc.path.toLowerCase().includes(searchLower)
    )
  }, [docs, searchText])

  const filters = [
    { value: '', label: 'すべて' },
    { value: 'enriched', label: '追加コンテンツあり' },
    { value: 'transcript', label: '文字起こしあり' },
    { value: 'pdf', label: 'PDFテキストあり' },
    { value: 'link', label: 'リンクコンテンツあり' },
  ]

  return (
    <main className="min-h-screen bg-gray-100">
      <Header />
      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Stats */}
        {stats && (
          <div className="grid grid-cols-4 gap-4 mb-6">
            <div className="bg-white rounded-lg p-4 border border-gray-200 shadow-sm">
              <div className="text-2xl font-bold text-gray-700">{docs.length}</div>
              <div className="text-sm text-gray-500">総ドキュメント</div>
            </div>
            <div className="bg-white rounded-lg p-4 border border-gray-200 shadow-sm">
              <div className="text-2xl font-bold text-purple-600">{stats.withTranscripts}</div>
              <div className="text-sm text-gray-500">🎬 文字起こし</div>
            </div>
            <div className="bg-white rounded-lg p-4 border border-gray-200 shadow-sm">
              <div className="text-2xl font-bold text-blue-600">{stats.withPdfText}</div>
              <div className="text-sm text-gray-500">📑 PDF</div>
            </div>
            <div className="bg-white rounded-lg p-4 border border-gray-200 shadow-sm">
              <div className="text-2xl font-bold text-green-600">{stats.withLinkContent}</div>
              <div className="text-sm text-gray-500">🔗 リンク</div>
            </div>
          </div>
        )}

        {/* Search and Filter */}
        <div className="bg-white rounded-lg p-4 border border-gray-200 shadow-sm mb-6">
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
            <div className="flex border border-gray-300 rounded-md overflow-hidden">
              <button
                onClick={() => setViewMode('category')}
                className={`px-3 py-2 text-sm ${viewMode === 'category' ? 'bg-blue-500 text-white' : 'bg-white text-gray-600'}`}
              >
                カテゴリ
              </button>
              <button
                onClick={() => setViewMode('tree')}
                className={`px-3 py-2 text-sm ${viewMode === 'tree' ? 'bg-blue-500 text-white' : 'bg-white text-gray-600'}`}
              >
                ツリー
              </button>
            </div>
          </div>
        </div>

        {/* Content */}
        {loading ? (
          <div className="text-center py-12 text-gray-500">読み込み中...</div>
        ) : viewMode === 'category' ? (
          /* Category View */
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {CATEGORIES.map(category => (
              <CategoryCard key={category.name} category={category} docs={filteredDocs} />
            ))}
          </div>
        ) : (
          /* Tree View */
          <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-4">
            <div className="space-y-1">
              {Array.from(new Set(filteredDocs.map(d => d.path.split('/')[0]))).sort().map(folder => (
                <TreeItem
                  key={folder}
                  title={folder}
                  docs={filteredDocs.filter(d => d.path.split('/')[0] === folder)}
                />
              ))}
            </div>
          </div>
        )}
      </div>
    </main>
  )
}
