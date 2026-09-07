import { Show, createMemo } from "solid-js"
import { RGBA } from "@opentui/core"
import { type Theme, generateSyntax } from "../theme"
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

  if (isUser()) {
    return (
      <box
        border={["left"]}
        borderColor={props.theme.primary}
        customBorderChars={{
          topLeft: "",
          bottomLeft: "",
          vertical: "┃",
          topRight: "",
          bottomRight: "",
          horizontal: " ",
          bottomT: "",
          topT: "",
          cross: "",
          leftT: "",
          rightT: "",
        }}
        marginTop={1}
        marginBottom={1}
      >
        <box
          paddingTop={1}
          paddingBottom={1}
          paddingLeft={2}
          paddingRight={2}
          backgroundColor={props.theme.backgroundPanel}
          flexShrink={0}
        >
          <text fg={props.theme.text}>{props.message.content}</text>
        </box>
      </box>
    )
  }

  if (isSystem()) {
    return (
      <box
        flexDirection="column"
        paddingLeft={3}
        marginTop={1}
        marginBottom={1}
        flexShrink={0}
      >
        <text fg={props.theme.textMuted}>{props.message.content}</text>
      </box>
    )
  }

  const syntax = createMemo(() => generateSyntax(props.theme))

  // Assistant Message
  return (
    <box
      flexDirection="column"
      marginTop={1}
      marginBottom={1}
      flexShrink={0}
    >
      {/* Thinking Header (Collapsible OpenCode Style with animated spinner) */}
      <Show when={props.message.thinking}>
        <box flexDirection="row" paddingLeft={3}>
          <Show
            when={props.message.isStreaming}
            fallback={<text fg={props.theme.warning}>+ Thought: {props.message.thinking}</text>}
          >
            <Spinner color={props.theme.warning}>Thinking...</Spinner>
          </Show>
        </box>
      </Show>

      {/* Main Content Body with Markdown Rendering */}
      <Show when={props.message.content && props.message.content.length > 0}>
        <box flexDirection="column" paddingLeft={3} marginTop={1}>
          <markdown
            content={props.message.content}
            syntaxStyle={syntax()}
            fg={props.theme.markdownText}
          />
        </box>
      </Show>

      {/* OpenCode Model / Timing Execution Badge */}
      <Show when={!props.message.isStreaming}>
        <box flexDirection="row" paddingLeft={3} marginTop={1}>
          <text fg={props.theme.textMuted}>
            <span style={{ fg: props.theme.primary }}>▣ Build</span> · {props.message.stats || "Qwen 2.5 3B (GPU) · 1.4s"}
          </text>
        </box>
      </Show>
    </box>
  )
}
