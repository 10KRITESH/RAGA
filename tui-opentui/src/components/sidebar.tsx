import { For, Show, createMemo } from "solid-js"
import { RGBA } from "@opentui/core"
import type { Theme } from "../theme"

export type SourceItem = {
  id: number
  path: string
  score: number
  chunkText: string
}

function getFileTypeBadge(filePath: string): { label: string; color: string; icon: string } {
  const ext = filePath.slice(filePath.lastIndexOf(".")).toLowerCase()
  switch (ext) {
    case ".pdf":
      return { label: "PDF", color: "#fc533a", icon: "📄" }
    case ".docx":
    case ".doc":
      return { label: "DOCX", color: "#3b5cf6", icon: "📝" }
    case ".py":
      return { label: "PY", color: "#38bdf8", icon: "⚡" }
    case ".ts":
    case ".tsx":
    case ".js":
    case ".jsx":
      return { label: "JS/TS", color: "#fcd53a", icon: "⚡" }
    case ".md":
      return { label: "MD", color: "#c83d8b", icon: "📜" }
    case ".csv":
    case ".xlsx":
    case ".xls":
      return { label: "DATA", color: "#12c905", icon: "📊" }
    default:
      return { label: "TXT", color: "#a0a0a0", icon: "📄" }
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
  const filled = Math.min(6, Math.max(0, Math.round((pct / 100) * 6)))
  const bar = "█".repeat(filled) + "░".repeat(6 - filled)
  return { bar, pct }
}

export function Sidebar(props: {
  theme: Theme
  sources: SourceItem[]
  selectedIndex: number
  onSelect: (index: number) => void
}) {
  const selectedSource = createMemo(() => {
    return props.sources[props.selectedIndex] || props.sources[0] || null
  })

  return (
    <box
      backgroundColor={props.theme.backgroundPanel}
      width={42}
      height="100%"
      flexDirection="column"
      paddingTop={1}
      paddingBottom={1}
      paddingLeft={1}
      paddingRight={1}
    >
      {/* ── Header ── */}
      <box paddingBottom={1} paddingLeft={1} flexShrink={0}>
        <text fg={props.theme.text}>
          <b>📦 SOURCES ({props.sources.length})</b>
        </text>
      </box>

      {/* ── Top Half: Sources List ── */}
      <scrollbox
        height="50%"
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
          fallback={
            <box paddingLeft={1}>
              <text fg={props.theme.textMuted}>No sources referenced yet.</text>
              <text fg={props.theme.textMuted}>Ask a question to see retrieved files.</text>
            </box>
          }
        >
          <box flexDirection="column" gap={1}>
            <For each={props.sources}>
              {(src, idx) => {
                const badge = getFileTypeBadge(src.path)
                const name = getFileName(src.path)
                const folder = getRelativeFolder(src.path)
                const meter = renderMeter(src.score)
                const isSelected = createMemo(() => props.selectedIndex === idx())

                return (
                  <box
                    flexDirection="column"
                    paddingLeft={1}
                    paddingRight={1}
                    paddingTop={0}
                    paddingBottom={0}
                    backgroundColor={isSelected() ? props.theme.backgroundElement : undefined}
                    onMouseDown={() => props.onSelect(idx())}
                  >
                    {/* Top Row: Index + Badge + Filename */}
                    <box flexDirection="row" gap={1} justifyContent="space-between">
                      <box flexDirection="row" gap={1}>
                        <text fg={isSelected() ? props.theme.primary : props.theme.textMuted}>
                          <b>{idx() + 1}.</b>
                        </text>
                        <text fg={RGBA.fromHex(badge.color)}>
                          <b>[{badge.label}]</b>
                        </text>
                        <text fg={props.theme.text}>
                          <b>{name.length > 14 ? name.slice(0, 13) + "…" : name}</b>
                        </text>
                      </box>

                      {/* Relevance Meter */}
                      <text fg={meter.pct >= 70 ? props.theme.success : props.theme.warning}>
                        {meter.bar} {meter.pct}%
                      </text>
                    </box>

                    {/* Folder path */}
                    <Show when={folder}>
                      <text fg={props.theme.textMuted}>   📁 {folder}/</text>
                    </Show>
                  </box>
                )
              }}
            </For>
          </box>
        </Show>
      </scrollbox>

      {/* ── Mid Divider ── */}
      <box
        height={1}
        flexShrink={0}
        paddingTop={0}
        paddingBottom={0}
        justifyContent="center"
      >
        <text fg={props.theme.border}>────────────────────────────────────────</text>
      </box>

      {/* ── Bottom Half Header: Chunk Preview ── */}
      <box paddingBottom={0} paddingTop={0} paddingLeft={1} flexShrink={0}>
        <text fg={props.theme.text}>
          <b>📄 CHUNK PREVIEW</b>
        </text>
      </box>

      {/* ── Bottom Half Content: Preview Box ── */}
      <scrollbox
        flexGrow={1}
        paddingLeft={1}
        paddingRight={1}
        paddingTop={1}
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
              No source selected. Run a query or press 1-5 to inspect.
            </text>
          }
        >
          {(src) => {
            const badge = getFileTypeBadge(src().path)
            const name = getFileName(src().path)
            const folder = getRelativeFolder(src().path)
            return (
              <box flexDirection="column" gap={1}>
                <text fg={props.theme.text}>
                  <b>{badge.icon} {name}</b>
                </text>
                <text fg={props.theme.textMuted}>📁 {folder ? folder + "/" : "root"}</text>
                <text fg={props.theme.border}>────────────────────────────────────</text>
                <text fg={props.theme.textMuted}>{src().chunkText}</text>
              </box>
            )
          }}
        </Show>
      </scrollbox>

      {/* ── Footer ── */}
      <box flexShrink={0} paddingTop={1} paddingLeft={1}>
        <text fg={props.theme.textMuted}>
          <span style={{ fg: props.theme.success }}>•</span> <b>RAGA</b>{" "}
          <span style={{ fg: props.theme.text }}>
            <b>Intelligence</b>
          </span>{" "}
          <span>1.0.0</span>
        </text>
      </box>
    </box>
  )
}
