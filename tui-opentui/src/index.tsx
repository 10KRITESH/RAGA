import { render } from "@opentui/solid"
import { createCliRenderer } from "@opentui/core"
import { App } from "./app"

const renderer = await createCliRenderer({
  exitOnCtrlC: false,
})

render(() => <App />, renderer)
