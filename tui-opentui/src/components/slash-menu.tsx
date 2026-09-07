import { TextAttributes } from "@opentui/core"
import { createMemo, For, Show } from "solid-js"
import { type Theme, selectedForeground } from "../theme"

export interface SlashCommand {
  name: string
  description: string
  action: () => void
}

export function SlashMenu(props: {
  theme: Theme
  query: string
  selectedIndex: number
  commands: SlashCommand[]
  onSelect: (cmd: SlashCommand) => void
  onHover: (index: number) => void
}) {
  const filtered = createMemo(() => {
    const q = props.query.toLowerCase().trim()
    if (!q || q === "/") return props.commands
    const matchStr = q.startsWith("/") ? q : `/${q}`
    return props.commands.filter(
      (c) =>
        c.name.toLowerCase().includes(matchStr) ||
        c.description.toLowerCase().includes(q.replace(/^\//, ""))
    )
  })

  return (
    <box
      flexDirection="column"
      backgroundColor={props.theme.backgroundMenu}
      border={["top", "bottom", "left", "right"]}
      borderColor={props.theme.border}
      paddingLeft={1}
      paddingRight={1}
      paddingTop={0}
      paddingBottom={0}
      width="100%"
      maxHeight={12}
    >
      <Show
        when={filtered().length > 0}
        fallback={
          <box paddingLeft={1} paddingRight={1} paddingTop={1} paddingBottom={1}>
            <text fg={props.theme.textMuted}>No matching commands</text>
          </box>
        }
      >
        <For each={filtered().slice(0, 10)}>
          {(cmd, index) => {
            const isSelected = () => index() === props.selectedIndex
            const fg = () => (isSelected() ? selectedForeground(props.theme) : props.theme.text)
            const descFg = () => (isSelected() ? selectedForeground(props.theme) : props.theme.textMuted)

            return (
              <box
                flexDirection="row"
                justifyContent="space-between"
                backgroundColor={isSelected() ? props.theme.primary : undefined}
                paddingLeft={1}
                paddingRight={1}
                onMouseDown={() => props.onSelect(cmd)}
                onMouseOver={() => props.onHover(index())}
              >
                <box flexDirection="row" gap={2}>
                  <text
                    fg={fg()}
                    attributes={isSelected() ? TextAttributes.BOLD : undefined}
                  >
                    {cmd.name.padEnd(14, " ")}
                  </text>
                  <text fg={descFg()}>
                    {cmd.description}
                  </text>
                </box>
              </box>
            )
          }}
        </For>
      </Show>
    </box>
  )
}
