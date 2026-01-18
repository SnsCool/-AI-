import { NextResponse } from 'next/server'
import fs from 'fs'
import path from 'path'

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

function scanNotionDocs(dirPath: string, basePath: string = ''): NotionDoc[] {
  const docs: NotionDoc[] = []

  try {
    const items = fs.readdirSync(dirPath)

    for (const item of items) {
      const fullPath = path.join(dirPath, item)
      const stat = fs.statSync(fullPath)

      if (stat.isDirectory()) {
        const indexPath = path.join(fullPath, 'index.md')
        const relativePath = path.join(basePath, item)

        if (fs.existsSync(indexPath)) {
          // Count associated content files
          const files = fs.readdirSync(fullPath)
          const transcripts = files.filter(f => f.endsWith('_transcript.txt'))
          const pdfTexts = files.filter(f => f.endsWith('_text.txt'))
          const linkContents = files.filter(f => f.startsWith('link_') && f.endsWith('_content.txt'))

          docs.push({
            id: Buffer.from(relativePath).toString('base64url'),
            title: item,
            path: relativePath,
            hasTranscript: transcripts.length > 0,
            hasPdfText: pdfTexts.length > 0,
            hasLinkContent: linkContents.length > 0,
            transcriptCount: transcripts.length,
            pdfTextCount: pdfTexts.length,
            linkContentCount: linkContents.length,
          })
        }

        // Recursively scan subdirectories
        docs.push(...scanNotionDocs(fullPath, relativePath))
      }
    }
  } catch (error) {
    console.error('Error scanning directory:', dirPath, error)
  }

  return docs
}

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url)
  const search = searchParams.get('search') || ''
  const filter = searchParams.get('filter') || ''

  const notionDocsPath = path.join(process.cwd(), '..', 'notion_docs')
  let docs = scanNotionDocs(notionDocsPath)

  // Apply search filter
  if (search) {
    const searchLower = search.toLowerCase()
    docs = docs.filter(doc =>
      doc.title.toLowerCase().includes(searchLower) ||
      doc.path.toLowerCase().includes(searchLower)
    )
  }

  // Apply content filter
  if (filter === 'transcript') {
    docs = docs.filter(doc => doc.hasTranscript)
  } else if (filter === 'pdf') {
    docs = docs.filter(doc => doc.hasPdfText)
  } else if (filter === 'link') {
    docs = docs.filter(doc => doc.hasLinkContent)
  } else if (filter === 'enriched') {
    docs = docs.filter(doc => doc.hasTranscript || doc.hasPdfText || doc.hasLinkContent)
  }

  // Sort by path for better organization
  docs.sort((a, b) => a.path.localeCompare(b.path))

  return NextResponse.json({
    docs,
    total: docs.length,
    stats: {
      withTranscripts: docs.filter(d => d.hasTranscript).length,
      withPdfText: docs.filter(d => d.hasPdfText).length,
      withLinkContent: docs.filter(d => d.hasLinkContent).length,
    }
  })
}
