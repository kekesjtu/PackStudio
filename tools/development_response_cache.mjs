export default function developmentResponseCache(request, response, next) {
  const path = request.url?.split('?')[0] ?? ''
  const isLiveModule = path.startsWith('/src/frontend/') || path === '/@vite/client'
    || path === '/@react-refresh' || path.endsWith('/vite/dist/client/env.mjs')
  const isDocument = path === '/' || path.endsWith('.html')
  if (isLiveModule || isDocument) {
    // Development sources change between runs; retain caching for versioned dependencies.
    delete request.headers['if-none-match']
    delete request.headers['if-modified-since']
    const setHeader = response.setHeader
    response.setHeader = function (name, value) {
      return setHeader.call(this, name, name.toLowerCase() === 'cache-control' ? 'no-store' : value)
    }
    response.setHeader('Cache-Control', 'no-store')
  }
  next()
}
