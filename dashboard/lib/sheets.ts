import { google } from 'googleapis'

// スプレッドシートID（Zoom相談一覧）
const SPREADSHEET_ID = process.env.SPREADSHEET_ID || '1R5oMbJ7E-QfDFhHR164y8JKs6XLnkJcw8zBm2IPSn8E'
const SHEET_NAME = 'Zoom相談一覧'

export interface MeetingData {
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

async function getGoogleSheetsClient() {
  const credentials = {
    client_email: process.env.GOOGLE_SERVICE_ACCOUNT_EMAIL,
    private_key: process.env.GOOGLE_PRIVATE_KEY?.replace(/\\n/g, '\n'),
  }

  const auth = new google.auth.GoogleAuth({
    credentials,
    scopes: ['https://www.googleapis.com/auth/spreadsheets.readonly'],
  })

  const sheets = google.sheets({ version: 'v4', auth })
  return sheets
}

export async function getMeetings(): Promise<MeetingData[]> {
  try {
    const sheets = await getGoogleSheetsClient()

    const response = await sheets.spreadsheets.values.get({
      spreadsheetId: SPREADSHEET_ID,
      range: `${SHEET_NAME}!A:H`,
    })

    const rows = response.data.values
    if (!rows || rows.length < 2) {
      return []
    }

    // ヘッダー行をスキップしてデータを変換
    const meetings: MeetingData[] = rows.slice(1).map((row, index) => ({
      id: index + 2, // 行番号（ヘッダー + 1から開始）
      customerName: row[0] || '',
      assignee: row[1] || '',
      meetingDatetime: row[2] || '',
      duration: row[3] || '',
      status: row[4] || '',
      transcriptUrl: row[5] || '',
      videoUrl: row[6] || '',
      feedback: row[7] || '',
    }))

    // 空の行を除外
    return meetings.filter(m => m.customerName || m.assignee)
  } catch (error) {
    console.error('Google Sheets API エラー:', error)
    throw error
  }
}

export async function getMeetingById(id: number): Promise<MeetingData | null> {
  const meetings = await getMeetings()
  return meetings.find(m => m.id === id) || null
}
