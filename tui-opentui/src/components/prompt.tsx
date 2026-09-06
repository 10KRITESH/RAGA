import { createSignal, Show } from "solid-js"
import { RGBA } from "@opentui/core"
import type { Theme } from "../theme"

export function Prompt(props: {
  theme: Theme
  onSubmit: (text: string) => void
  directory: string
  disabled?: boolean
}) {
  const [value, setValue] = createSignal("")

  const handleInput = (char: string) => {
    setValue((prev) => prev + char)
  }

  const handleBackspace = () => {
    setValue((prev) => prev.slice(0, -1))
  }

  const handleSubmit = () => {
    const text = value().trim()
    if (!text || props.disabled) return
    setValue("")
    props.onSubmit(text)
  }

  return (
    <box flexDirection="column" paddingLeft={2} paddingRight={2} paddingBottom={1} flexShrink={0}>
      {/* ── Elevated Prompt Box ── */}
      <box
        backgroundColor={props.theme.backgroundPanel}
        borderLeftColor={props.theme.primary}
        paddingLeft={2}
        paddingRight={2}
        paddingTop={1}
        paddingBottom={1}
        flexDirection="column"
      >
        {/* Input Line */}
        <box flexDirection="row" gap={1}>
          <text fg={props.theme.primary}><b>│</b></text>
          <Show
            when={value().length > 0}
            fallback={
              <text fg={props.theme.textMuted}>
                Ask a question about your files, mention @file, or type /themes, /status, /help...
              </text>
            }
          >
            <text fg={props.theme.text}>{value()}</text>
          </Show>
          <text fg={props.theme.primary}>█</text>
        </box>

        {/* Model Tag Line */}
        <box paddingTop={1} flexDirection="row" gap={2}>
          <text fg={props.theme.textMuted}>
            <span style={{ fg: props.theme.primary }}><b>Query</b></span> · Qwen 2.5 3B (Local GPU) · nomic-embed-text · <span style={{ fg: props.theme.warning }}>hybrid</span>
          </text>
        </box>
      </box>

      {/* ── Bottom Status Line ── */}
      <box flexDirection="row" justifyContent="space-between" paddingTop={1}>
        <text fg={props.theme.textMuted}>{props.directory}</text>
        <box flexDirection="row" gap={2}>
          <text fg={props.theme.textMuted}>
            <span style={{ fg: props.theme.text }}>ctrl+p</span> commands · <span style={{ fg: props.theme.text }}>1-5</span> preview sources · <span style={{ fg: props.theme.text }}>ctrl+c</span> quit
          </text>
        </box>
      </box>
    </box>
  )
}
