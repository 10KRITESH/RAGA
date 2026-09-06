/**
 * System and Terminal Clipboard Helper for OpenTUI
 * Supports Wayland (wl-copy), X11 (xclip), and OSC 52 ANSI escape sequences.
 */

export function copyToClipboard(text: string): boolean {
  if (!text) return false

  let copied = false

  // 1. Wayland wl-copy
  try {
    const proc = Bun.spawn(["wl-copy"], { stdin: "pipe", stdout: "ignore", stderr: "ignore" })
    proc.stdin.write(text)
    proc.stdin.end()
    copied = true
  } catch {}

  // 2. X11 xclip
  if (!copied) {
    try {
      const proc = Bun.spawn(["xclip", "-selection", "clipboard"], { stdin: "pipe", stdout: "ignore", stderr: "ignore" })
      proc.stdin.write(text)
      proc.stdin.end()
      copied = true
    } catch {}
  }

  // 3. OSC 52 terminal clipboard sequence (universal fallback)
  try {
    const b64 = Buffer.from(text).toString("base64")
    process.stdout.write(`\x1b]52;c;${b64}\x07`)
    copied = true
  } catch {}

  return copied
}
