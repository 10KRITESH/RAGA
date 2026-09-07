import { createSignal, createMemo, For, Show } from "solid-js"
import { useKeyboard } from "@opentui/solid"
import { RGBA } from "@opentui/core"
import type { Theme } from "../theme"

export type PaletteCommand = {
  id: string
  title: string
  category: string
  action: () => void
}

export function CommandPalette(props: {
  theme: Theme
  commands: PaletteCommand[]
  category?: string
  title?: string
  placeholder?: string
  onClose: () => void
}) {
  const [filter, setFilter] = createSignal("")
  const [selectedIndex, setSelectedIndex] = createSignal(0)

  const scopedCommands = createMemo(() => {
    if (!props.category) return props.commands
    return props.commands.filter(
      (c) => c.category.toLowerCase() === props.category?.toLowerCase()
    )
  })

  const filtered = createMemo(() => {
    const q = filter().toLowerCase().trim()
    if (!q) return scopedCommands()
    return scopedCommands().filter(
      (c) =>
        c.title.toLowerCase().includes(q) ||
        c.category.toLowerCase().includes(q) ||
        c.id.toLowerCase().includes(q)
    )
  })

  useKeyboard((e) => {
    if (e.name === "escape") {
      props.onClose()
      return
    }
    if (e.name === "up") {
      setSelectedIndex((prev) => Math.max(0, prev - 1))
      return
    }
    if (e.name === "down") {
      setSelectedIndex((prev) => Math.min(filtered().length - 1, prev + 1))
      return
    }
    if (e.name === "return" || e.name === "enter") {
      const item = filtered()[selectedIndex()]
      if (item) {
        item.action()
        props.onClose()
      }
      return
    }
    if (e.name === "backspace") {
      setFilter((prev) => prev.slice(0, -1))
      setSelectedIndex(0)
      return
    }
    if (e.name === "space") {
      setFilter((prev) => prev + " ")
      setSelectedIndex(0)
      return
    }
    if (e.raw && e.raw.length === 1 && !e.ctrl) {
      setFilter((prev) => prev + e.raw)
      setSelectedIndex(0)
    }
  })

  const placeholderText = () => {
    if (props.placeholder) return props.placeholder
    if (props.category) return `Search ${props.category.toLowerCase()}s...`
    return "Type a command, theme, or model..."
  }

  return (
    <box
      position="absolute"
      top={4}
      left="20%"
      width="60%"
      maxHeight={20}
      backgroundColor={props.theme.backgroundPanel}
      border={["top", "bottom", "left", "right"]}
      borderColor={props.theme.primary}
      paddingLeft={2}
      paddingRight={2}
      paddingTop={1}
      paddingBottom={1}
      flexDirection="column"
      zIndex={2000}
    >
      {/* Search Header */}
      <box flexDirection="row" gap={1} paddingBottom={1}>
        <text fg={props.theme.primary}><b>&gt;</b></text>
        <Show
          when={filter().length > 0}
          fallback={<text fg={props.theme.textMuted}>{placeholderText()}</text>}
        >
          <text fg={props.theme.text}>{filter()}</text>
        </Show>
        <text fg={props.theme.primary}>█</text>
      </box>

      {/* Results List */}
      <scrollbox
        flexGrow={1}
        paddingTop={1}
        verticalScrollbarOptions={{
          trackOptions: {
            backgroundColor: props.theme.background,
            foregroundColor: props.theme.borderActive,
          },
        }}
      >
        <Show
          when={filtered().length > 0}
          fallback={
            <box paddingLeft={1} paddingRight={1} paddingTop={1}>
              <text fg={props.theme.textMuted}>No matching options</text>
            </box>
          }
        >
          <For each={filtered()}>
            {(cmd, idx) => {
              const isSelected = createMemo(() => selectedIndex() === idx())
              return (
                <box
                  flexDirection="row"
                  justifyContent="space-between"
                  paddingLeft={1}
                  paddingRight={1}
                  paddingTop={0}
                  paddingBottom={0}
                  backgroundColor={isSelected() ? props.theme.backgroundElement : undefined}
                  onMouseDown={() => {
                    cmd.action()
                    props.onClose()
                  }}
                >
                  <box flexDirection="row" gap={1}>
                    <text fg={isSelected() ? props.theme.primary : props.theme.textMuted}>
                      {isSelected() ? "›" : " "}
                    </text>
                    <text fg={isSelected() ? props.theme.text : props.theme.textMuted}>
                      <b>{cmd.title}</b>
                    </text>
                  </box>
                  <text fg={props.theme.textMuted}>{cmd.category}</text>
                </box>
              )
            }}
          </For>
        </Show>
      </scrollbox>

      {/* Footer Info */}
      <box flexDirection="row" justifyContent="space-between" paddingTop={1}>
        <text fg={props.theme.textMuted}>
          <span style={{ fg: props.theme.text }}>↑/↓</span> navigate · <span style={{ fg: props.theme.text }}>Enter</span> select · <span style={{ fg: props.theme.text }}>Esc</span> close
        </text>
      </box>
    </box>
  )
}
