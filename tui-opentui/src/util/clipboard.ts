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

export async function readFromClipboard(): Promise<string> {
  // 1. Wayland wl-paste
  try {
    const proc = Bun.spawn(["wl-paste", "--no-newline"], { stdout: "pipe", stderr: "ignore" })
    const text = await new Response(proc.stdout).text()
    if (text && text.length > 0) return text
  } catch {}

  // 2. X11 xclip
  try {
    const proc = Bun.spawn(["xclip", "-selection", "clipboard", "-o"], { stdout: "pipe", stderr: "ignore" })
    const text = await new Response(proc.stdout).text()
    if (text && text.length > 0) return text
  } catch {}

  // 3. xsel
  try {
    const proc = Bun.spawn(["xsel", "--clipboard", "--output"], { stdout: "pipe", stderr: "ignore" })
    const text = await new Response(proc.stdout).text()
    if (text && text.length > 0) return text
  } catch {}

  return ""
}

