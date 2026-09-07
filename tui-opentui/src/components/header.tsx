import type { Theme } from "../theme"

export function Header(props: { theme: Theme; fileCount: number; modelName: string; toastMsg?: string }) {
  return (
    <box
      backgroundColor={props.theme.backgroundPanel}
      height={3}
      flexShrink={0}
      flexDirection="row"
      alignItems="center"
      justifyContent="space-between"
      paddingLeft={2}
      paddingRight={2}
    >
      <box flexDirection="row" gap={2} alignItems="center">
        <text fg={props.theme.primary}>
          <b>◈  R A G A</b> <span style={{ fg: props.theme.textMuted }}>[#1 Session]</span>
        </text>
        <text fg={props.theme.textMuted}>
          · 🧠 {props.modelName}
        </text>
      </box>

      <box flexDirection="row" gap={2} alignItems="center">
        {props.toastMsg ? (
          <text fg={props.theme.success}>
            ✔ <b>{props.toastMsg}</b>
          </text>
        ) : (
          <box flexDirection="row" gap={1} alignItems="center">
            <text fg={props.theme.success}>
              ● <b>ONLINE</b>
            </text>
            <text fg={props.theme.textMuted}>
              · {props.fileCount.toLocaleString()} files indexed
            </text>
          </box>
        )}
      </box>
    </box>
  )
}
