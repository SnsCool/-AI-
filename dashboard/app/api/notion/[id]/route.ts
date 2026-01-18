import { NextResponse } from 'next/server'
import fs from 'fs'
import path from 'path'

interface AssociatedContent {
  type: 'transcript' | 'pdf_text' | 'link_content'
  filename: string
  content: string
  title?: string
}

export async function GET(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params

  // Decode the base64url path
  let docPath: string
  try {
    docPath = Buffer.from(id, 'base64url').toString('utf-8')
  } catch {
    return NextResponse.json({ error: 'Invalid document ID' }, { status: 400 })
  }

  const notionDocsPath = path.join(process.cwd(), '..', 'notion_docs')
  const fullPath = path.join(notionDocsPath, docPath)

  // Security check - ensure path is within notion_docs
  if (!fullPath.startsWith(notionDocsPath)) {
    return NextResponse.json({ error: 'Invalid path' }, { status: 403 })
  }

  const indexPath = path.join(fullPath, 'index.md')

  if (!fs.existsSync(indexPath)) {
    return NextResponse.json({ error: 'Document not found' }, { status: 404 })
  }

  // Read main document
  const mainContent = fs.readFileSync(indexPath, 'utf-8')

  // Read associated content files
  const associatedContent: AssociatedContent[] = []
  const files = fs.readdirSync(fullPath)

  for (const file of files) {
    const filePath = path.join(fullPath, file)

    if (file.endsWith('_transcript.txt')) {
      const content = fs.readFileSync(filePath, 'utf-8')
      associatedContent.push({
        type: 'transcript',
        filename: file,
        content,
        title: extractTitle(content) || file.replace('_transcript.txt', '')
      })
    } else if (file.endsWith('_text.txt')) {
      const content = fs.readFileSync(filePath, 'utf-8')
      associatedContent.push({
        type: 'pdf_text',
        filename: file,
        content,
        title: extractTitle(content) || file.replace('_text.txt', '')
      })
    } else if (file.startsWith('link_') && file.endsWith('_content.txt')) {
      const content = fs.readFileSync(filePath, 'utf-8')
      associatedContent.push({
        type: 'link_content',
        filename: file,
        content,
        title: extractTitle(content) || file.replace('link_', '').replace('_content.txt', '')
      })
    }
  }

  // Sort associated content by type
  associatedContent.sort((a, b) => {
    const order = { transcript: 0, pdf_text: 1, link_content: 2 }
    return order[a.type] - order[b.type]
  })

  return NextResponse.json({
    doc: {
      id,
      title: path.basename(docPath),
      path: docPath,
      content: mainContent,
      associatedContent,
      stats: {
        transcripts: associatedContent.filter(c => c.type === 'transcript').length,
        pdfTexts: associatedContent.filter(c => c.type === 'pdf_text').length,
        linkContents: associatedContent.filter(c => c.type === 'link_content').length,
      }
    }
  })
}

function extractTitle(content: string): string | undefined {
  // Try to extract title from markdown header
  const match = content.match(/^#\s+(.+)$/m)
  if (match) {
    return match[1].trim()
  }

  // Try to extract from **Title**: format
  const titleMatch = content.match(/\*\*(?:タイトル|動画タイトル|Title)\*\*:\s*(.+)$/m)
  if (titleMatch) {
    return titleMatch[1].trim()
  }

  return undefined
}
