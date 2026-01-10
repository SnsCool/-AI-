'use client'

import { useState, useEffect } from 'react'
import Header from '@/components/Header'
import SearchFilter from '@/components/SearchFilter'
import MeetingList from '@/components/MeetingList'

export interface Meeting {
  id: number
  customerName: string
  assignee: string
  meetingDatetime: string
  duration: string
  status: string
  transcriptUrl: string
  videoUrl: string
  feedback: string
}

export default function Home() {
  const [meetings, setMeetings] = useState<Meeting[]>([])
  const [filteredMeetings, setFilteredMeetings] = useState<Meeting[]>([])
  const [loading, setLoading] = useState(true)
  const [searchText, setSearchText] = useState('')
  const [selectedAssignee, setSelectedAssignee] = useState('')
  const [assignees, setAssignees] = useState<string[]>([])

  useEffect(() => {
    fetchMeetings()
  }, [])

  useEffect(() => {
    filterMeetings()
  }, [meetings, searchText, selectedAssignee])

  const fetchMeetings = async () => {
    try {
      const res = await fetch('/api/meetings')
      const data = await res.json()
      setMeetings(data.meetings || [])

      // 担当者リストを抽出
      const uniqueAssignees = [...new Set(data.meetings?.map((m: Meeting) => m.assignee) || [])] as string[]
      setAssignees(uniqueAssignees)
    } catch (error) {
      console.error('データ取得エラー:', error)
    } finally {
      setLoading(false)
    }
  }

  const filterMeetings = () => {
    let filtered = [...meetings]

    if (searchText) {
      filtered = filtered.filter(m =>
        m.customerName?.includes(searchText) ||
        m.assignee?.includes(searchText) ||
        m.feedback?.includes(searchText)
      )
    }

    if (selectedAssignee) {
      filtered = filtered.filter(m => m.assignee === selectedAssignee)
    }

    setFilteredMeetings(filtered)
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-gray-600">読み込み中...</div>
      </div>
    )
  }

  return (
    <main className="min-h-screen">
      <Header />
      <div className="max-w-6xl mx-auto px-4 py-6">
        <SearchFilter
          searchText={searchText}
          onSearchChange={setSearchText}
          selectedAssignee={selectedAssignee}
          onAssigneeChange={setSelectedAssignee}
          assignees={assignees}
        />
        <MeetingList meetings={filteredMeetings} />
      </div>
    </main>
  )
}
