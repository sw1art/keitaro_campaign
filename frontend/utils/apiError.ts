/**
 * Unified API error used by both the real HTTP client and the mock.
 * Mirrors the backend error shape `{ error: { code, message } }`.
 */
export class ApiError extends Error {
  readonly code: string
  readonly status: number

  constructor(code: string, message: string, status = 0) {
    super(message)
    this.name = 'ApiError'
    this.code = code
    this.status = status
  }
}
