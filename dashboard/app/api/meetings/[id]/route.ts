import { NextResponse } from 'next/server'
import { getMeetingById } from '@/lib/sheets'

export async function GET(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params
    const meetingId = parseInt(id, 10)
    if (isNaN(meetingId)) {
      return NextResponse.json(
        { error: '無効なIDです' },
        { status: 400 }
      )
    }

    const meeting = await getMeetingById(meetingId)
    if (!meeting) {
      return NextResponse.json(
        { error: '面談が見つかりません' },
        { status: 404 }
      )
    }

    return NextResponse.json({ meeting })
  } catch (error) {
    console.error('面談データ取得エラー:', error)
    return NextResponse.json(
      { error: 'データの取得に失敗しました' },
      { status: 500 }
    )
  }
}
