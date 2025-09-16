import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import Table from '@/components/Common/Table'

interface TestData {
  id: number
  name: string
  value: number
}

const mockData: TestData[] = [
  { id: 1, name: 'Item 1', value: 100 },
  { id: 2, name: 'Item 2', value: 200 },
]

const columns = [
  { key: 'name' as keyof TestData, header: 'Name' },
  { key: 'value' as keyof TestData, header: 'Value' },
]

describe('Table', () => {
  it('renders table with data', () => {
    render(<Table data={mockData} columns={columns} />)

    expect(screen.getByText('Name')).toBeInTheDocument()
    expect(screen.getByText('Value')).toBeInTheDocument()
    expect(screen.getByText('Item 1')).toBeInTheDocument()
    expect(screen.getByText('100')).toBeInTheDocument()
  })

  it('renders empty message when no data', () => {
    render(<Table data={[]} columns={columns} emptyMessage="No items found" />)

    expect(screen.getByText('No items found')).toBeInTheDocument()
  })

  it('shows loading spinner when loading', () => {
    render(<Table data={[]} columns={columns} loading />)

    expect(screen.getByRole('status')).toBeInTheDocument()
  })
})
