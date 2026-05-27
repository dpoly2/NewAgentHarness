/**
 * Centralized logger using winston with daily rotating log files.
 * Logs go to data/logs/YYYY-MM-DD.log and also to console.
 */
const path = require('path')
const fs = require('fs')
const winston = require('winston')
require('winston-daily-rotate-file')

const LOG_DIR = path.join(__dirname, '..', '..', 'data', 'logs')
if (!fs.existsSync(LOG_DIR)) fs.mkdirSync(LOG_DIR, { recursive: true })

const { combine, timestamp, printf, colorize, errors } = winston.format

const logFormat = printf(({ level, message, timestamp, stack }) => {
  return `${timestamp} [${level.toUpperCase()}] ${stack || message}`
})

const fileTransport = new winston.transports.DailyRotateFile({
  dirname: LOG_DIR,
  filename: '%DATE%.log',
  datePattern: 'YYYY-MM-DD',
  maxFiles: '14d',   // keep 2 weeks of logs
  maxSize: '20m',
  zippedArchive: true,
  format: combine(timestamp(), errors({ stack: true }), logFormat)
})

const consoleTransport = new winston.transports.Console({
  format: combine(colorize(), timestamp({ format: 'HH:mm:ss' }), errors({ stack: true }), logFormat)
})

const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  transports: [fileTransport, consoleTransport]
})

/**
 * Replace console.log/warn/error with logger so all output goes to file too.
 * Call once at server startup.
 */
function patchConsole() {
  const orig = { log: console.log, warn: console.warn, error: console.error, info: console.info }
  console.log   = (...a) => logger.info(a.map(String).join(' '))
  console.info  = (...a) => logger.info(a.map(String).join(' '))
  console.warn  = (...a) => logger.warn(a.map(String).join(' '))
  console.error = (...a) => logger.error(a.map(String).join(' '))
  return orig // return originals in case caller wants to restore
}

// GET /api/settings/logs endpoint helper — return recent log lines
function getRecentLogs(lines = 100) {
  try {
    const d = new Date()
    const today = `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`
    const logFile = path.join(LOG_DIR, `${today}.log`)
    if (!fs.existsSync(logFile)) return []
    const content = fs.readFileSync(logFile, 'utf8')
    const all = content.split('\n').filter(l => l.trim())
    return all.slice(-lines)
  } catch (e) { return [] }
}

module.exports = { logger, patchConsole, getRecentLogs }
