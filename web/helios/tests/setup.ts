import ResizeObserver from 'resize-observer-polyfill'
import { afterAll, afterEach, beforeAll } from 'vitest'

import { server } from './mocks/server'

const JSDOM_VIEWPORT_WIDTH = 1024
const JSDOM_VIEWPORT_HEIGHT = 768

globalThis.ResizeObserver = ResizeObserver
Object.defineProperty(window, 'visualViewport', {
  configurable: true,
  value: Object.assign(new EventTarget(), {
    width: JSDOM_VIEWPORT_WIDTH,
    height: JSDOM_VIEWPORT_HEIGHT,
    scale: 1,
    offsetLeft: 0,
    offsetTop: 0,
    pageLeft: 0,
    pageTop: 0,
  }),
})

beforeAll(() => server.listen({ onUnhandledFrame: 'error' }))
afterEach(() => server.resetHandlers())
afterAll(() => server.close())
