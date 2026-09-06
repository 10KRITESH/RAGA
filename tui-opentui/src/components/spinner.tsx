import { createSignal, onCleanup, Show } from "solid-js"
import type { RGBA } from "@opentui/core"
import type { JSX } from "@opentui/solid"

export const SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

export function Spinner(props: { label?: string; children?: any; color?: RGBA }) {
  const [frame, setFrame] = createSignal(0)
  const timer = setInterval(() => {
    setFrame((prev) => (prev + 1) % SPINNER_FRAMES.length)
  }, 80)
  onCleanup(() => clearInterval(timer))

  const textContent = () => {
    if (typeof props.children === "string") return props.children
    if (props.label) return props.label
    return ""
  }

  return (
    <box flexDirection="row" gap={1}>
      <text fg={props.color}>{SPINNER_FRAMES[frame()]}</text>
      <Show when={textContent()}>
        <text fg={props.color}>{textContent()}</text>
      </Show>
    </box>
  )
}
