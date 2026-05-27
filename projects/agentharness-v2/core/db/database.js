/**
 * Database layer — uses better-sqlite3 if available, falls back to JSON files
 * No native build required in fallback mode.
 */
const path = require('path')
const fs = require('fs')

const DATA_DIR = path.join(__dirname, '..', '..', 'data')
if (!fs.existsSync(DATA_DIR)) fs.mkdirSync(DATA_DIR, { recursive: true })

// ─── Try better-sqlite3 ───────────────────────────────────────────
let betterSqlite = null
try { betterSqlite = require('better-sqlite3') } catch (e) { /* use JSON fallback */ }

if (betterSqlite) {
  const DB_PATH = path.join(DATA_DIR, 'agentharness.db')
  const SCHEMA_PATH = path.join(__dirname, 'schema.sql')
  let db = null

  function getDb() {
    if (db) return db
    db = new betterSqlite(DB_PATH)
    db.pragma('journal_mode = WAL')
    db.pragma('foreign_keys = ON')
    db.exec(fs.readFileSync(SCHEMA_PATH, 'utf8'))
    return db
  }
  function generateId() { return Date.now().toString(36) + Math.random().toString(36).slice(2, 7) }
  module.exports = { getDb, generateId }
  return
}

// ─── JSON-file fallback database ─────────────────────────────────
// Mimics the better-sqlite3 synchronous interface
const tables = {}
const TABLE_FILES = ['conversations','messages','agent_tasks','todos','agent_memory','projects','notifications','daily_briefs','automations']

function loadTable(name) {
  const fp = path.join(DATA_DIR, `${name}.json`)
  try { tables[name] = JSON.parse(fs.readFileSync(fp, 'utf8')) } catch (e) { if (!tables[name]) tables[name] = [] }
  return tables[name]
}

function saveTable(name) {
  const fp = path.join(DATA_DIR, `${name}.json`)
  fs.writeFileSync(fp, JSON.stringify(tables[name] || [], null, 2))
}

function generateId() { return Date.now().toString(36) + Math.random().toString(36).slice(2, 7) }

function now() { return new Date().toISOString().replace('T', ' ').slice(0, 19) }

// SQL→JSON interpreter — supports basic SELECT/INSERT/UPDATE/DELETE
function parseSql(sql) {
  sql = sql.trim().replace(/\s+/g, ' ')
  if (/^SELECT/i.test(sql)) return { type: 'select', sql }
  if (/^INSERT/i.test(sql)) return { type: 'insert', sql }
  if (/^UPDATE/i.test(sql)) return { type: 'update', sql }
  if (/^DELETE/i.test(sql)) return { type: 'delete', sql }
  return { type: 'other', sql }
}

function getTableName(sql) {
  const m = sql.match(/(?:FROM|INTO|UPDATE|TABLE)\s+([a-z_]+)/i)
  return m ? m[1].toLowerCase() : null
}

function applyWhere(rows, whereStr, params) {
  if (!whereStr) return rows
  const conditions = whereStr.split(/\s+AND\s+/i).map(c => c.trim())
  let paramIdx = 0
  return rows.filter(row => {
    for (const cond of conditions) {
      // NOT IN ('a','b') support
      const notInM = cond.match(/([a-z_]+)\s+NOT\s+IN\s*\(([^)]+)\)/i)
      if (notInM) {
        const col = notInM[1]
        const vals = notInM[2].split(',').map(v => v.trim().replace(/^'|'$/g, ''))
        if (vals.includes(String(row[col]))) return false
        continue
      }
      // IN ('a','b') support
      const inM = cond.match(/([a-z_]+)\s+IN\s*\(([^)]+)\)/i)
      if (inM) {
        const col = inM[1]
        const vals = inM[2].split(',').map(v => v.trim().replace(/^'|'$/g, ''))
        if (!vals.includes(String(row[col]))) return false
        continue
      }
      const m = cond.match(/([a-z_]+)\s*([=!<>]+)\s*(\?|'[^']*'|date\([^)]*\))/i)
      if (!m) continue
      const col = m[1]; const op = m[2]; const valStr = m[3]
      let val = valStr === '?' ? params[paramIdx++] : valStr.replace(/^'|'$/g, '')
      const rowVal = row[col]
      if (op === '=' && String(rowVal) !== String(val)) return false
      if (op === '!=' && String(rowVal) === String(val)) return false
      if (op === '<>' && String(rowVal) === String(val)) return false
    }
    return true
  })
}

// Create a prepared-statement-like object
function makeStmt(sql) {
  return {
    run(...params) {
      const flat = params.flat()
      const { type } = parseSql(sql)
      const tableName = getTableName(sql)
      if (!tableName) return { changes: 0 }

      if (type === 'insert') {
        const rows = loadTable(tableName)
        const colMatch = sql.match(/\(([^)]+)\)\s+VALUES/i)
        const cols = colMatch ? colMatch[1].split(',').map(c => c.trim()) : []
        if (cols.length && flat.length >= cols.length) {
          const row = {}
          cols.forEach((c, i) => { row[c] = flat[i] })
          // Auto-add timestamps if not provided
          if (!row.created_at) row.created_at = now()
          if (!row.updated_at) row.updated_at = now()
          // ON CONFLICT DO UPDATE
          if (/ON CONFLICT/i.test(sql) && /DO UPDATE/i.test(sql)) {
            const conflictMatch = sql.match(/UNIQUE\(([^)]+)\)/)
            let conflicts = conflictMatch ? conflictMatch[1].split(',').map(c => c.trim()) : []
            if (!conflicts.length) {
              // Try to find unique key from primary key
              const pkCol = cols[0] // assume first col is PK
              conflicts = [pkCol]
            }
            const existIdx = rows.findIndex(r => conflicts.every(c => String(r[c]) === String(row[c])))
            if (existIdx >= 0) {
              const setMatch = sql.match(/DO UPDATE SET (.+)$/i)
              if (setMatch) {
                const updates = setMatch[1].split(',').map(s => s.trim())
                for (const upd of updates) {
                  const eqM = upd.match(/([a-z_]+)\s*=\s*excluded\.([a-z_]+)/i)
                  if (eqM) rows[existIdx][eqM[1]] = row[eqM[2]]
                  const dtM = upd.match(/([a-z_]+)\s*=\s*datetime\('now'\)/i)
                  if (dtM) rows[existIdx][dtM[1]] = now()
                }
              }
            } else {
              rows.push(row)
            }
          } else if (/OR IGNORE/i.test(sql)) {
            const pkCol = cols[0]
            if (!rows.find(r => String(r[pkCol]) === String(row[pkCol]))) rows.push(row)
          } else {
            // Default INSERT: skip if primary key already exists (prevent duplicates)
            const pkCol = cols[0]
            if (!rows.find(r => String(r[pkCol]) === String(row[pkCol]))) {
              rows.push(row)
            }
          }
          saveTable(tableName)
        }
        return { changes: 1, lastInsertRowid: flat[0] }
      }

      if (type === 'update') {
        const rows = loadTable(tableName)
        const setMatch = sql.match(/SET\s+(.+?)(?:\s+WHERE\s+(.+))?$/i)
        if (!setMatch) return { changes: 0 }
        const setStr = setMatch[1]; const whereStr = setMatch[2] || ''
        const toUpdate = applyWhere(rows, whereStr, flat.slice(-1))

        let paramIdx = 0
        const pairs = setStr.split(/,(?![^(]*\))/).map(s => s.trim())
        for (const row of toUpdate) {
          for (const pair of pairs) {
            const eq = pair.match(/([a-z_]+)\s*=\s*(\?|datetime\('now'\)|[^,]+)/i)
            if (!eq) continue
            const col = eq[1]; const valStr = eq[2].trim()
            if (valStr === '?') row[col] = flat[paramIdx++]
            else if (/datetime\('now'\)/i.test(valStr)) row[col] = now()
            else row[col] = valStr.replace(/^'|'$/g, '')
          }
        }
        saveTable(tableName)
        return { changes: toUpdate.length }
      }

      if (type === 'delete') {
        const rows = loadTable(tableName)
        const whereMatch = sql.match(/WHERE\s+(.+)$/i)
        const whereStr = whereMatch ? whereMatch[1] : ''
        const before = rows.length
        const toKeep = whereStr ? rows.filter(r => !applyWhere([r], whereStr, flat).length) : []
        tables[tableName] = toKeep
        saveTable(tableName)
        return { changes: before - toKeep.length }
      }

      return { changes: 0 }
    },

    get(...params) {
      const flat = params.flat()
      const tableName = getTableName(sql)
      if (!tableName) return null
      const rows = loadTable(tableName)
      const whereMatch = sql.match(/WHERE\s+(.+?)(?:\s+ORDER|\s+LIMIT|$)/i)
      const whereStr = whereMatch ? whereMatch[1] : ''
      const filtered = applyWhere(rows, whereStr, flat)

      // COUNT(*) query — always return count even if 0
      if (/COUNT\(\*\)\s+as\s+([a-z_]+)/i.test(sql)) {
        const alias = sql.match(/COUNT\(\*\)\s+as\s+([a-z_]+)/i)[1]
        return { [alias]: filtered.length }
      }

      if (!filtered.length) return null
      return filtered[0]
    },

    all(...params) {
      const flat = params.flat()
      const tableName = getTableName(sql)
      if (!tableName) return []
      const rows = loadTable(tableName)

      const whereMatch = sql.match(/WHERE\s+(.+?)(?:\s+ORDER|\s+LIMIT|\s+GROUP|$)/i)
      const whereStr = whereMatch ? whereMatch[1] : ''
      let filtered = applyWhere(rows, whereStr, flat)

      // GROUP BY (simplified — just return unique project_slugs with counts)
      if (/GROUP BY/i.test(sql)) {
        const groupMatch = sql.match(/GROUP BY\s+([a-z_]+)/i)
        const groupCol = groupMatch ? groupMatch[1] : null
        if (groupCol) {
          const groups = {}
          for (const r of filtered) {
            const key = r[groupCol] || 'null'
            if (!groups[key]) groups[key] = { [groupCol]: r[groupCol], total: 0, open: 0, urgent: 0, count: 0 }
            groups[key].count++; groups[key].total++
            if (r.status && !['done','cancelled'].includes(r.status)) groups[key].open++
            if (['urgent','high'].includes(r.priority) && !['done','cancelled'].includes(r.status)) groups[key].urgent++
          }
          return Object.values(groups)
        }
      }

      // ORDER BY (simplified)
      const orderMatch = sql.match(/ORDER BY\s+(.+?)(?:\s+LIMIT|$)/i)
      if (orderMatch) {
        const orderStr = orderMatch[1]
        if (/priority/i.test(orderStr)) {
          const PRIO = { urgent: 1, high: 2, medium: 3, low: 4 }
          filtered.sort((a, b) => (PRIO[a.priority] || 5) - (PRIO[b.priority] || 5))
        } else if (/created_at DESC/i.test(orderStr) || /updated_at DESC/i.test(orderStr)) {
          const col = /updated_at/i.test(orderStr) ? 'updated_at' : 'created_at'
          filtered.sort((a, b) => (b[col] || '').localeCompare(a[col] || ''))
        } else if (/created_at ASC/i.test(orderStr)) {
          filtered.sort((a, b) => (a.created_at || '').localeCompare(b.created_at || ''))
        }
      }

      // LIMIT
      const limitMatch = sql.match(/LIMIT\s+(\d+)/i)
      if (limitMatch) filtered = filtered.slice(0, parseInt(limitMatch[1]))

      return filtered
    }
  }
}

function getDb() {
  // Ensure all tables loaded
  TABLE_FILES.forEach(t => loadTable(t))
  return { prepare: makeStmt, exec: () => {} }
}

module.exports = { getDb, generateId }
