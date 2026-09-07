import { For, Show, createMemo } from "solid-js"
import { RGBA } from "@opentui/core"
import type { Theme } from "../theme"

export type SourceItem = {
  id: number
  path: string
  score: number
  chunkText: string
}

function getFileTypeBadge(filePath: string): { label: string; color: string } {
  const ext = filePath.slice(filePath.lastIndexOf(".")).toLowerCase()
  switch (ext) {
    case ".pdf":
      return { label: "PDF", color: "#fc533a" }
    case ".docx":
    case ".doc":
      return { label: "DOCX", color: "#3b5cf6" }
    case ".py":
      return { label: "PY", color: "#38bdf8" }
    case ".ts":
    case ".tsx":
    case ".js":
    case ".jsx":
      return { label: "JS", color: "#fcd53a" }
    case ".md":
      return { label: "MD", color: "#c83d8b" }
    case ".csv":
    case ".xlsx":
    case ".xls":
      return { label: "DATA", color: "#12c905" }
    default:
      return { label: "TXT", color: "#a0a0a0" }
  }
}

function getFileName(filePath: string): string {
  const parts = filePath.split("/")
  return parts[parts.length - 1] || filePath
}

function getRelativeFolder(filePath: string): string {
  const parts = filePath.split("/")
  if (parts.length <= 1) return ""
  return parts.slice(-3, -1).join("/")
}

function renderMeter(score: number): { bar: string; pct: number } {
  const pct = Math.min(100, Math.max(0, Math.round(score * 100)))
  const filled = Math.min(5, Math.max(0, Math.round((pct / 100) * 5)))
  const bar = "█".repeat(filled) + "░".repeat(5 - filled)
  return { bar, pct }
}

export function Sidebar(props: {
  theme: Theme
  sources: SourceItem[]
  selectedIndex: number
  fileCount: number
  onSelect: (index: number) => void
}) {
  const selectedSource = createMemo(() => {
    return props.sources[props.selectedIndex] || props.sources[0] || null
  })

  return (
    <box
      width={36}
      height="100%"
      flexDirection="column"
      paddingTop={1}
      paddingBottom={1}
      paddingLeft={2}
      paddingRight={1}
      gap={1}
    >
      {/* ── Section 1: Session / Title ── */}
      <box flexDirection="column" flexShrink={0} marginBottom={1}>
        <text fg={props.theme.text}><b>Greeting</b></text>
      </box>

      {/* ── Section 2: Context / System Telemetry ── */}
      <box flexDirection="column" flexShrink={0} marginBottom={1} gap={0}>
        <text fg={props.theme.text}><b>Context</b></text>
        <text fg={props.theme.textMuted}>{props.fileCount.toLocaleString()} files indexed</text>
        <text fg={props.theme.textMuted}>Qwen 2.5 3B (GPU)</text>
        <text fg={props.theme.textMuted}>Hybrid RAG + ReRank</text>
      </box>

      {/* ── Section 3: Sources ── */}
      <box flexDirection="column" flexShrink={0}>
        <text fg={props.theme.text}>
          <b>Sources ({props.sources.length})</b>
        </text>
      </box>

      <scrollbox
        height={8}
        flexShrink={0}
        paddingRight={1}
        verticalScrollbarOptions={{
          trackOptions: {
            backgroundColor: props.theme.background,
            foregroundColor: props.theme.borderActive,
          },
        }}
      >
        <Show
          when={props.sources.length > 0}
          fallback={<text fg={props.theme.textMuted}>No sources referenced</text>}
        >
          <box flexDirection="column" gap={1}>
            <For each={props.sources}>
              {(src, idx) => {
                const badge = getFileTypeBadge(src.path)
                const name = getFileName(src.path)
                const meter = renderMeter(src.score)
                const isSelected = createMemo(() => props.selectedIndex === idx())

                return (
                  <box
                    flexDirection="column"
                    paddingLeft={0}
                    paddingRight={0}
                    onMouseDown={() => props.onSelect(idx())}
                  >
                    <box flexDirection="row" justifyContent="space-between">
                      <box flexDirection="row" gap={1}>
                        <text fg={isSelected() ? props.theme.primary : props.theme.textMuted}>
                          {idx() + 1}.
                        </text>
                        <text fg={isSelected() ? props.theme.text : props.theme.textMuted}>
                          {name.length > 14 ? name.slice(0, 13) + "…" : name}
                        </text>
                      </box>
                      <text fg={meter.pct >= 75 ? props.theme.success : props.theme.warning}>
                        {meter.pct}%
                      </text>
                    </box>
                  </box>
                )
              }}
            </For>
          </box>
        </Show>
      </scrollbox>

      {/* ── Section 4: Chunk Preview ── */}
      <box flexDirection="column" flexShrink={0} marginTop={1}>
        <text fg={props.theme.text}><b>Preview</b></text>
      </box>

      <scrollbox
        flexGrow={1}
        paddingRight={1}
        verticalScrollbarOptions={{
          trackOptions: {
            backgroundColor: props.theme.background,
            foregroundColor: props.theme.borderActive,
          },
        }}
      >
        <Show
          when={selectedSource()}
          fallback={
            <text fg={props.theme.textMuted}>
              Select 1-{props.sources.length || 5} to inspect chunk
            </text>
          }
        >
          {(src) => {
            const name = getFileName(src().path)
            const folder = getRelativeFolder(src().path)
            return (
              <box flexDirection="column" gap={0}>
                <text fg={props.theme.primary}>{name}</text>
                <text fg={props.theme.textMuted}>{folder ? folder + "/" : ""}</text>
                <text fg={props.theme.textMuted}>{src().chunkText}</text>
              </box>
            )
          }}
        </Show>
      </scrollbox>

      {/* ── Footer ── */}
      <box flexShrink={0} paddingTop={1} flexDirection="column">
        <text fg={props.theme.textMuted}>/~</text>
        <text fg={props.theme.textMuted}>
          <span style={{ fg: props.theme.success }}>•</span> RAGA 1.0.0
        </text>
      </box>
    </box>
  )
}
