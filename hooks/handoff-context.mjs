#!/usr/bin/env node
// Read-only bounded context, shared by the installed hook and on-demand callers.
import fs from "node:fs"
import { StringDecoder } from "node:string_decoder"
import { fileURLToPath } from "node:url"
import { performance } from "node:perf_hooks"

export const MAX_CONTEXT_BYTES = 8192
const MAX_SCAN_BYTES = 4 * 1024 * 1024
const MAX_LINE_BYTES = 16 * 1024
const MAX_SCAN_MS = 1000
const SOURCE = "docs/handoff/HANDOFF.md"
const titles = ["Next actions", "Open items & blockers", "Decisions & context"]
const aliases = [
  ["next actions", "next steps", "다음 작업", "다음 행동", "다음 할 일", "후속 작업", "다음 액션"],
  ["open items & blockers", "open items and blockers", "open items / blockers", "미해결 항목", "미해결 문제", "미해결 항목 및 차단 사항", "미해결 항목 및 블로커", "미해결 사항 및 블로커", "미해결 사항 및 차단 사항", "미해결 및 차단 사항", "미해결 / 블로커"],
  ["decisions & context", "decisions and context", "decisions / context", "결정 및 맥락", "결정 사항 및 맥락", "결정사항 및 맥락", "결정 및 배경", "결정 / 컨텍스트"],
]
const normalizeTitle = title => title.replace(/\s+#+$/, "").replace(/\s*([/&])\s*/g, " $1 ").replace(/\s+/g, " ").trim().toLowerCase()
const historicalTitles = new Set(["(이전)", "이전", "history", "completed", "archive", "archives", "(history)", "(completed)", "이력", "보관", "완료"])
const bytes = text => Buffer.byteLength(text, "utf8")
const prefix = (text, limit) => new StringDecoder("utf8").write(Buffer.from(text).subarray(0, Math.max(0, limit)))

export function readHandoffContext(file) {
  let fd
  try {
    // A standalone caller may pass a FIFO: never block before the regular-file check.
    fd = fs.openSync(file, fs.constants.O_RDONLY | fs.constants.O_NONBLOCK)
    const stat = fs.fstatSync(fd)
    if (!stat.isFile()) throw new Error("not a regular file")
    const sections = new Map()
    let active = null
    let fence = null
    let historicalLevel = null
    let anyTruncated = stat.size > MAX_SCAN_BYTES
    const handleLine = (buffer, shortened) => {
      const line = new StringDecoder("utf8").write(buffer).replace(/\r$/, "")
      const fenceMark = line.match(/^ {0,3}(`{3,}|~{3,})(.*)$/)
      if (fence) {
        if (fenceMark && fenceMark[1][0] === fence.char && fenceMark[1].length >= fence.length && !fenceMark[2].trim()) fence = null
      } else if (fenceMark && !(fenceMark[1][0] === "`" && fenceMark[2].includes("`"))) {
        fence = { char: fenceMark[1][0], length: fenceMark[1].length }
      } else if (!shortened) {
        const heading = line.match(/^ {0,3}(#{1,6})\s+(.+?)\s*$/)
        if (heading) {
          const level = heading[1].length
          const title = normalizeTitle(heading[2])
          if (historicalLevel !== null) {
            if (level > historicalLevel) return
            historicalLevel = null
          }
          if (active && level <= active.level) active = null
          if (historicalTitles.has(title)) {
            historicalLevel = level
            return
          }
          const kind = aliases.findIndex(values => values.includes(title))
          if (kind !== -1 && (!sections.has(kind) || level <= sections.get(kind).level)) {
            active = { kind, level, text: "", truncated: false }
            // Prefer canonical outer sections; the last same-level occurrence wins.
            sections.set(kind, active)
            return
          }
        }
      }
      if (active && historicalLevel === null) {
        const remaining = MAX_CONTEXT_BYTES - bytes(active.text)
        const addition = `${line}\n`
        active.text += prefix(addition, remaining)
        active.truncated ||= shortened || bytes(addition) > remaining
      }
      anyTruncated ||= shortened
    }
    const chunk = Buffer.alloc(16 * 1024)
    let scanned = 0
    let pending = Buffer.alloc(0)
    let shortened = false
    const scanLimit = Math.min(stat.size, MAX_SCAN_BYTES)
    const started = performance.now()
    let deadlineReached = false
    while (scanned < scanLimit) {
      if (performance.now() - started >= MAX_SCAN_MS) {
        deadlineReached = true
        break
      }
      const count = fs.readSync(fd, chunk, 0, Math.min(chunk.length, scanLimit - scanned), null)
      if (!count) break
      scanned += count
      let start = 0
      while (start < count) {
        const newline = chunk.indexOf(10, start)
        const end = newline === -1 || newline >= count ? count : newline
        const segment = chunk.subarray(start, end)
        const available = MAX_LINE_BYTES - pending.length
        pending = Buffer.concat([pending, segment.subarray(0, available)])
        shortened ||= segment.length > available
        if (end < count) {
          handleLine(pending, shortened)
          pending = Buffer.alloc(0)
          shortened = false
        }
        start = end + 1
      }
    }
    if (pending.length || shortened) handleLine(pending, shortened || stat.size > scanned)
    anyTruncated ||= deadlineReached
    let output = `[인계 요약] source: ${SOURCE}\nLatest shallowest recognized sections within scanned content; history excluded, original unchanged.\n`
    if (deadlineReached) output += "[truncated] Scan time budget reached (1 s); later sections may be missing or newer.\n"
    else if (stat.size > MAX_SCAN_BYTES) output += "[truncated] Scan capped at 4 MiB; later sections may be missing or newer.\n"
    const found = [0, 1, 2].filter(kind => sections.has(kind))
    if (!found.length) return output + "[생략] No recognized current sections; read relevant source sections on demand.\n"
    // Reserve explicit notice space; allocate all three sections with action/blocker priority.
    const notice = "[truncated] Context limited to 8 KiB; read the source for omitted details.\n"
    const remaining = MAX_CONTEXT_BYTES - bytes(output) - bytes(notice) - 1
    const weights = [0.45, 0.35, 0.20]
    const totalWeight = found.reduce((sum, kind) => sum + weights[kind], 0)
    const allocations = found.map(kind => {
      const section = sections.get(kind)
      const content = `\n## ${titles[kind]}\n${section.text.trim() || "(empty)"}\n`
      return { section, content, budget: Math.min(bytes(content), Math.floor(remaining * weights[kind] / totalWeight)) }
    })
    let spare = remaining - allocations.reduce((sum, item) => sum + item.budget, 0)
    for (const item of allocations) {
      const extra = Math.min(spare, bytes(item.content) - item.budget)
      item.budget += extra
      spare -= extra
      output += prefix(item.content, item.budget)
      anyTruncated ||= item.section.truncated || bytes(item.content) > item.budget
    }
    if (anyTruncated) output += `\n${notice}`
    return output
  } catch {
    return `[인계 생략] source: ${SOURCE} — unavailable; no full-file fallback.\n`
  } finally {
    if (fd !== undefined) fs.closeSync(fd)
  }
}

if (process.argv[1] && fs.realpathSync(process.argv[1]) === fileURLToPath(import.meta.url)) {
  process.stdout.write(readHandoffContext(process.argv[2]))
}
