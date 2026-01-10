import { NextResponse } from 'next/server'
import { getMeetings } from '@/lib/sheets'

export async function GET() {
  try {
    const meetings = await getMeetings()
    return NextResponse.json({ meetings })
  } catch (error) {
    console.error('面談データ取得エラー:', error)
    return NextResponse.json(
      { error: 'データの取得に失敗しました' },
      { status: 500 }
    )
  }
}
