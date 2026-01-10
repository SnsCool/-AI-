'use client'

import Link from 'next/link'
import type { Meeting } from '@/app/page'

interface MeetingListProps {
  meetings: Meeting[]
}

export default function MeetingList({ meetings }: MeetingListProps) {
  if (meetings.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        面談記録がありません
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {meetings.map((meeting) => (
        <Link
          key={meeting.id}
          href={`/meeting/${meeting.id}`}
          className="block bg-white rounded-lg shadow-sm border border-gray-200 p-4 hover:shadow-md transition-shadow"
        >
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-2">
            <div>
              <h3 className="text-lg font-semibold text-gray-800">
                {meeting.customerName || '顧客名未設定'} 様
              </h3>
              <div className="text-sm text-gray-600 mt-1">
                <span>担当: {meeting.assignee}</span>
                <span className="mx-2">|</span>
                <span>{meeting.meetingDatetime}</span>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-sm text-gray-500">
                {meeting.duration}
              </span>
              {meeting.status && (
                <span className={`px-2 py-1 text-xs rounded-full ${
                  meeting.status === '成約'
                    ? 'bg-green-100 text-green-800'
                    : meeting.status === '失注'
                    ? 'bg-red-100 text-red-800'
                    : 'bg-gray-100 text-gray-800'
                }`}>
                  {meeting.status}
                </span>
              )}
            </div>
          </div>
        </Link>
      ))}
    </div>
  )
}
