import { defineConfig } from 'vite'
import path from 'node:path'

export default defineConfig({
  base: './',
  build: {
    rollupOptions: {
      input: path.resolve(__dirname, 'renderer/index.html')
    }
  }
})
