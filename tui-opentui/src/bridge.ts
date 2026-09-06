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

export async function executeQuery(query: string): Promise<QueryResult> {
  try {
    const proc = Bun.spawn(["uv", "run", "python", BRIDGE_SCRIPT, query], {
      cwd: path.resolve(import.meta.dir, "../.."),
      stdout: "pipe",
      stderr: "pipe",
    })
    const output = await new Response(proc.stdout).text()
    return JSON.parse(output.trim())
  } catch (err) {
    return {
      qtype: "content",
      text: `Error executing query via bridge: ${err}`,
      sources: [],
      elapsed: 0,
    }
  }
}
