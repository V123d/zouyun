import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        // 关闭代理缓冲，确保 SSE 事件流能实时透传到前端
        // 避免 LLM 长时间生成时 SSE 事件被 Vite 代理缓冲导致前端"卡住"
        configure: (proxy) => {
          proxy.on('proxyRes', (proxyRes) => {
            // 当响应是 SSE 流时，关闭代理层的缓冲
            if (proxyRes.headers['content-type']?.includes('text/event-stream')) {
              proxyRes.headers['cache-control'] = 'no-cache';
              proxyRes.headers['x-accel-buffering'] = 'no';
            }
          });
        },
      },
    },
  },
})
