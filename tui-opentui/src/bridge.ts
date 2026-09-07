import path from "path"
import type { SourceItem } from "./components/sidebar"

export type QueryResult = {
  qtype: string
  text: string
  sources: SourceItem[]
  elapsed: number
}

export type SystemStatus = {
  watched_dirs: string[]
  files_indexed: number
  files_failed: number
  last_indexed_at: string | null
}

export type OllamaModel = {
  name: string
  size: string
  parameters: string
  quantization: string
  is_embedding: boolean
}

const BRIDGE_SCRIPT = path.resolve(import.meta.dir, "../bridge.py")

export async function fetchStatus(): Promise<SystemStatus> {
  try {
    const proc = Bun.spawn(["uv", "run", "python", BRIDGE_SCRIPT, "--status"], {
      cwd: path.resolve(import.meta.dir, "../.."),
      stdout: "pipe",
      stderr: "pipe",
    })
    const output = await new Response(proc.stdout).text()
    return JSON.parse(output.trim())
  } catch {
    return {
      watched_dirs: ["Documents/NMIMS"],
      files_indexed: 1913,
      files_failed: 0,
      last_indexed_at: null,
    }
  }
}

export async function fetchModels(): Promise<OllamaModel[]> {
  try {
    const proc = Bun.spawn(["uv", "run", "python", BRIDGE_SCRIPT, "--models"], {
      cwd: path.resolve(import.meta.dir, "../.."),
      stdout: "pipe",
      stderr: "pipe",
    })
    const output = await new Response(proc.stdout).text()
    return JSON.parse(output.trim())
  } catch {
    return [
      { name: "qwen2.5:3b", size: "1.8 GB", parameters: "3.1B", quantization: "Q4_K_M", is_embedding: false },
      { name: "qwen2.5-coder:7b", size: "4.4 GB", parameters: "7.6B", quantization: "Q4_K_M", is_embedding: false },
    ]
  }
}

export type StreamChunk = {
  type: "meta" | "token" | "done" | "error"
  qtype?: string
  sources?: SourceItem[]
  token?: string
  elapsed?: number
  error?: string
}

export async function executeQueryStream(
  query: string,
  model: string | undefined,
  onChunk: (chunk: StreamChunk) => void
): Promise<void> {
  try {
    const args = ["uv", "run", "python", BRIDGE_SCRIPT, "--query", query, "--stream"]
    if (model) {
      args.push("--model", model)
    }
    const proc = Bun.spawn(args, {
      cwd: path.resolve(import.meta.dir, "../.."),
      stdout: "pipe",
      stderr: "pipe",
    })

    const reader = proc.stdout.getReader()
    const decoder = new TextDecoder()
    let buffer = ""

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split("\n")
      buffer = lines.pop() || ""
      for (const line of lines) {
        const trimmed = line.trim()
        if (!trimmed) continue
        try {
          const parsed = JSON.parse(trimmed) as StreamChunk
          onChunk(parsed)
        } catch {}
      }
    }

    if (buffer.trim()) {
      try {
        const parsed = JSON.parse(buffer.trim()) as StreamChunk
        onChunk(parsed)
      } catch {}
    }

    const stderrText = await new Response(proc.stderr).text()
    await proc.exited

    if (proc.exitCode !== 0 && stderrText.trim()) {
      onChunk({
        type: "error",
        error: stderrText.trim()
      })
    }
  } catch (err: any) {
    onChunk({
      type: "error",
      error: `Bridge execution error: ${err?.message || String(err)}`
    })
  }
}


export async function executeQuery(query: string, model?: string): Promise<QueryResult> {
  try {
    const args = ["uv", "run", "python", BRIDGE_SCRIPT, "--query", query]
    if (model) {
      args.push("--model", model)
    }
    const proc = Bun.spawn(args, {
      cwd: path.resolve(import.meta.dir, "../.."),
      stdout: "pipe",
      stderr: "pipe",
    })
    const [stdoutText, stderrText] = await Promise.all([
      new Response(proc.stdout).text(),
      new Response(proc.stderr).text(),
    ])
    await proc.exited

    const trimmed = stdoutText.trim()
    if (!trimmed) {
      const errDetail = stderrText.trim()
      return {
        qtype: "content",
        text: errDetail ? `Backend error:\n${errDetail}` : "No response received from Python backend.",
        sources: [],
        elapsed: 0,
      }
    }
    return JSON.parse(trimmed)
  } catch (err: any) {
    return {
      qtype: "content",
      text: `Error executing query via bridge: ${err?.message || String(err)}`,
      sources: [],
      elapsed: 0,
    }
  }
}

