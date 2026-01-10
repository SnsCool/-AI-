'use client'

interface SearchFilterProps {
  searchText: string
  onSearchChange: (text: string) => void
  selectedAssignee: string
  onAssigneeChange: (assignee: string) => void
  assignees: string[]
}

export default function SearchFilter({
  searchText,
  onSearchChange,
  selectedAssignee,
  onAssigneeChange,
  assignees,
}: SearchFilterProps) {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6">
      <div className="flex flex-col md:flex-row gap-4">
        <div className="flex-1">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            検索
          </label>
          <input
            type="text"
            value={searchText}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder="顧客名、担当者、内容で検索..."
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
        <div className="md:w-48">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            担当者
          </label>
          <select
            value={selectedAssignee}
            onChange={(e) => onAssigneeChange(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="">全員</option>
            {assignees.map((assignee) => (
              <option key={assignee} value={assignee}>
                {assignee}
              </option>
            ))}
          </select>
        </div>
      </div>
    </div>
  )
}
