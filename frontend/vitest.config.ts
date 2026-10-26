import { defineConfig, mergeConfig } from 'vitest/config';
import viteConfig from './vite.config';

// Node 25+ defines its own `localStorage` global, which is undefined without
// --localstorage-file and shadows the jsdom one the components use.
const nodeMajor = Number(process.versions.node.split('.')[0]);
const execArgv = nodeMajor >= 25 ? ['--no-experimental-webstorage'] : [];

export default mergeConfig(
  viteConfig,
  defineConfig({
    test: {
      environment: 'jsdom',
      include: ['src/**/*.test.{ts,tsx}'],
      setupFiles: ['src/test/setup.ts'],
      execArgv,
      coverage: {
        provider: 'v8',
        reporter: ['text-summary', 'lcov'],
        include: ['src/**/*.{ts,tsx}'],
        exclude: ['src/**/*.test.{ts,tsx}', 'src/test/**', 'src/main.tsx', 'src/vite-env.d.ts', 'src/components/ui/**'],
        // A floor a few points under the measured numbers; raise it as tests land.
        thresholds: { lines: 57, statements: 56, functions: 54, branches: 46 },
      },
    },
  }),
);
