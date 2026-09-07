import { RGBA } from "@opentui/core"
import { createSignal, onCleanup, onMount, For, Show } from "solid-js"
import { tint, type Theme } from "../theme"

export function ThinkingScanner(props: { theme: Theme; active?: boolean }) {
  const [frame, setFrame] = createSignal(0)
  const width = 8
  const holdStart = 10
  const holdEnd = 4
  const totalFrames = width + holdEnd + (width - 1) + holdStart

  onMount(() => {
    const timer = setInterval(() => {
      setFrame((prev) => (prev + 1) % totalFrames)
    }, 60)

    onCleanup(() => {
      clearInterval(timer)
    })
  })

  const getCells = () => {
    const frameIndex = frame()
    let activePos = 0
    if (frameIndex < width) {
      activePos = frameIndex
    } else if (frameIndex < width + holdEnd) {
      activePos = width - 1
    } else if (frameIndex < width + holdEnd + (width - 1)) {
      activePos = (width - 2) - (frameIndex - width - holdEnd)
    } else {
      activePos = 0
    }

    const cells: { char: string; color: RGBA }[] = []
    for (let c = 0; c < width; c++) {
      const dist = Math.abs(c - activePos)
      let char = "⬝"
      let factor = 0.25

      if (dist === 0) {
        char = "█"
        factor = 1.0
      } else if (dist === 1) {
        char = "▆"
        factor = 0.8
      } else if (dist === 2) {
        char = "◾"
        factor = 0.55
      } else if (dist === 3) {
        char = "▪"
        factor = 0.35
      }

      const col = tint(props.theme.background, props.theme.primary, factor)
      cells.push({ char, color: col })
    }
    return cells
  }

  return (
    <box flexDirection="row" gap={0} flexShrink={0}>
      <For each={getCells()}>
        {(cell) => (
          <text fg={cell.color} selectable={false}>
            {cell.char}
          </text>
        )}
      </For>
    </box>
  )
}
