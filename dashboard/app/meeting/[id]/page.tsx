'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Header from '@/components/Header'
import type { Meeting } from '@/app/page'

export default function MeetingDetail() {
  const params = useParams()
  const router = useRouter()
  const [meeting, setMeeting] = useState<Meeting | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchMeeting()
  }, [params.id])

  const fetchMeeting = async () => {
    try {
      const res = await fetch(`/api/meetings/${params.id}`)
      const data = await res.json()
      setMeeting(data.meeting)
    } catch (error) {
      console.error('データ取得エラー:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-gray-600">読み込み中...</div>
      </div>
    )
  }

  if (!meeting) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-gray-600">面談記録が見つかりません</div>
      </div>
    )
  }

  return (
    <main className="min-h-screen">
      <Header />
      <div className="max-w-4xl mx-auto px-4 py-6">
        <button
          onClick={() => router.back()}
          className="flex items-center text-gray-600 hover:text-gray-800 mb-6"
        >
          <span className="mr-1">←</span> 戻る
        </button>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-2xl font-bold text-gray-800 mb-4">
            {meeting.customerName || '顧客名未設定'} 様
          </h2>

          <div className="grid grid-cols-2 gap-4 mb-6 text-sm">
            <div>
              <span className="text-gray-500">担当者:</span>
              <span className="ml-2 text-gray-800">{meeting.assignee}</span>
            </div>
            <div>
              <span className="text-gray-500">面談日時:</span>
              <span className="ml-2 text-gray-800">{meeting.meetingDatetime}</span>
            </div>
            <div>
              <span className="text-gray-500">所要時間:</span>
              <span className="ml-2 text-gray-800">{meeting.duration}</span>
            </div>
            <div>
              <span className="text-gray-500">ステータス:</span>
              {meeting.status ? (
                <span className={`ml-2 px-2 py-1 text-xs rounded-full ${
                  meeting.status === '成約'
                    ? 'bg-green-100 text-green-800'
                    : meeting.status === '失注'
                    ? 'bg-red-100 text-red-800'
                    : 'bg-gray-100 text-gray-800'
                }`}>
                  {meeting.status}
                </span>
              ) : (
                <span className="ml-2 text-gray-400">未設定</span>
              )}
            </div>
          </div>

          <div className="flex gap-3 mb-6">
            {meeting.transcriptUrl && (
              <a
                href={meeting.transcriptUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors text-sm"
              >
                文字起こしを見る
              </a>
            )}
            {meeting.videoUrl && (
              <a
                href={meeting.videoUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 transition-colors text-sm"
              >
                動画を見る
              </a>
            )}
          </div>

          {meeting.feedback && (
            <div className="border-t border-gray-200 pt-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-4">
                フィードバック
              </h3>
              <div className="bg-gray-50 rounded-lg p-4 whitespace-pre-wrap text-sm text-gray-700 leading-relaxed">
                {meeting.feedback}
              </div>
            </div>
          )}
        </div>
      </div>
    </main>
  )
}
