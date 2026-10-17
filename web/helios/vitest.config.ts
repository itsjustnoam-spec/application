import { defineConfig, mergeConfig } from 'vitest/config'

import viteConfig from './vite.config.ts'

export default mergeConfig(
  viteConfig,
  defineConfig({
    test: {
      environment: 'jsdom',
      include: ['tests/unit/**/*.spec.ts', 'tests/integration/**/*.spec.ts'],
      setupFiles: ['tests/setup.ts'],
      restoreMocks: true,
      unstubGlobals: true,
      server: { deps: { inline: ['vuetify'] } },
      coverage: {
        provider: 'v8',
        reporter: ['text', 'cobertura'],
        include: ['src/**'],
      },
    },
  }),
)
