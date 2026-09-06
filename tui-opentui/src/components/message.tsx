import { Show } from "solid-js"
import { RGBA } from "@opentui/core"
import type { Theme } from "../theme"
import { Spinner } from "./spinner"

export type MessageItem = {
  id: string
  role: "user" | "assistant" | "system"
  content: string
  thinking?: string
  isStreaming?: boolean
  timestamp: string
  stats?: string
}

export function MessageCard(props: { message: MessageItem; theme: Theme }) {
  const isUser = () => props.message.role === "user"
  const isSystem = () => props.message.role === "system"

  const borderColor = () => {
    if (isUser()) return props.theme.primary
    if (isSystem()) return props.theme.warning
    return props.theme.accent
  }

  const roleLabel = () => {
    if (isUser()) return "You"
    if (isSystem()) return "RAGA  [SYSTEM]"
    return "RAGA  [CONTENT]"
  }

  return (
    <box
      flexDirection="column"
      backgroundColor={props.theme.backgroundPanel}
      paddingLeft={2}
      paddingRight={2}
      paddingTop={1}
      paddingBottom={1}
      marginBottom={1}
      borderLeftColor={borderColor()}
    >
      {/* ── Card Header ── */}
      <box flexDirection="row" justifyContent="space-between" paddingBottom={1}>
        <box flexDirection="row" gap={1}>
          <text fg={borderColor()}>
            <b>◈ {roleLabel()}</b>
          </text>
        </box>
        <text fg={props.theme.textMuted}>{props.message.timestamp}</text>
      </box>

      {/* ── Thinking / Tool Execution Block ── */}
      <Show when={props.message.thinking}>
        <box
          backgroundColor={props.theme.backgroundElement}
          paddingLeft={1}
          paddingRight={1}
          paddingTop={0}
          paddingBottom={0}
          marginBottom={1}
        >
          <Show
            when={props.message.isStreaming}
            fallback={<text fg={props.theme.textMuted}>+ Thought: {props.message.thinking}</text>}
          >
            <Spinner color={props.theme.warning} label={props.message.thinking} />
          </Show>
        </box>
      </Show>

      {/* ── Main Message Body ── */}
      <box flexDirection="column">
        <text fg={props.theme.text}>{props.message.content}</text>
      </box>

      {/* ── Stats Footer ── */}
      <Show when={props.message.stats}>
        <box paddingTop={1} borderTopColor={props.theme.borderSubtle}>
          <text fg={props.theme.textMuted}>{props.message.stats}</text>
        </box>
      </Show>
    </box>
  )
}
