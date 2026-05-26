/**
 * Input validation helpers for API routes.
 */

const MAX_MESSAGE_LENGTH = 8000
const MAX_TITLE_LENGTH = 200
const MAX_DESCRIPTION_LENGTH = 4000

function validateChat(req, res, next) {
  const { message, conversationId } = req.body
  if (!message || typeof message !== 'string') {
    return res.status(400).json({ error: 'message must be a non-empty string' })
  }
  if (message.length > MAX_MESSAGE_LENGTH) {
    return res.status(400).json({ error: `message too long (max ${MAX_MESSAGE_LENGTH} characters)` })
  }
  if (!conversationId || typeof conversationId !== 'string' || !/^[a-z0-9]+$/i.test(conversationId)) {
    return res.status(400).json({ error: 'invalid conversationId' })
  }
  next()
}

function validateTodo(req, res, next) {
  const { title } = req.body
  if (!title || typeof title !== 'string') {
    return res.status(400).json({ error: 'title is required' })
  }
  if (title.length > MAX_TITLE_LENGTH) {
    return res.status(400).json({ error: `title too long (max ${MAX_TITLE_LENGTH} characters)` })
  }
  next()
}

function sanitizeId(req, res, next) {
  const id = req.params.id || ''
  if (!/^[a-z0-9_-]+$/i.test(id)) {
    return res.status(400).json({ error: 'invalid id format' })
  }
  next()
}

module.exports = { validateChat, validateTodo, sanitizeId }
