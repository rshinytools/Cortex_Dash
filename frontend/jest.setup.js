import '@testing-library/jest-dom'

// Mock next/navigation
jest.mock('next/navigation', () => ({
  useRouter() {
    return {
      push: jest.fn(),
      replace: jest.fn(),
      prefetch: jest.fn(),
    }
  },
  useSearchParams() {
    return new URLSearchParams()
  },
  usePathname() {
    return ''
  },
}))

// Mock next/image
jest.mock('next/image', () => ({
  __esModule: true,
  default: (props) => {
    return <img {...props} />
  },
}))

// Mock ResizeObserver
global.ResizeObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
}))

// Mock IntersectionObserver
global.IntersectionObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
}))

// Mock matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(), // deprecated
    removeListener: jest.fn(), // deprecated
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
})

// Mock Chart.js
jest.mock('chart.js/auto', () => ({
  Chart: jest.fn().mockImplementation(() => ({
    update: jest.fn(),
    destroy: jest.fn(),
    render: jest.fn(),
  })),
}))

// Mock react-grid-layout
jest.mock('react-grid-layout', () => ({
  WidthProvider: (Component) => Component,
  Responsive: ({ children, ...props }) => <div {...props}>{children}</div>,
}))

// Setup test environment
beforeEach(() => {
  // Clear all mocks before each test
  jest.clearAllMocks()
})

// Global test utilities
global.createMockWidget = (overrides = {}) => ({
  id: 'test-widget-1',
  type: 'metric',
  title: 'Test Widget',
  position: { x: 0, y: 0, w: 4, h: 2 },
  config: {},
  ...overrides,
})

global.createMockDashboard = (overrides = {}) => ({
  id: 'test-dashboard-1',
  name: 'Test Dashboard',
  description: 'Test dashboard for testing',
  widgets: [],
  layout: { grid: { columns: 12, rows: 8 } },
  ...overrides,
})