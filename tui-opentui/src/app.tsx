import { createSignal, onMount, For, Show, createMemo } from "solid-js"
import { useTerminalDimensions, useRenderer, useKeyboard } from "@opentui/solid"
import { RGBA } from "@opentui/core"
import { resolveTheme, allThemes, type Theme } from "./theme"
import { Logo } from "./components/logo"
import { CommandPalette, type PaletteCommand } from "./components/command-palette"
import { Sidebar, type SourceItem } from "./components/sidebar"
import { MessageCard, type MessageItem } from "./components/message"
import { SlashMenu, type SlashCommand } from "./components/slash-menu"
import { ThinkingScanner } from "./components/thinking-scanner"
import { fetchStatus, fetchModels, executeQuery, executeQueryStream, type SystemStatus, type OllamaModel } from "./bridge"
import { copyToClipboard, readFromClipboard } from "./util/clipboard"
import { sessionEpilogue } from "./util/presentation"

const DEFAULT_THEME = "opencode"

export function App() {
  const dimensions = useTerminalDimensions()
  const renderer = useRenderer()
  const themes = allThemes()

  // ── Session Title State ──
  const [sessionTitle, setSessionTitle] = createSignal("New Session")

  // ── Toast / Clipboard State ──
  const [toastMsg, setToastMsg] = createSignal("")
  let toastTimer: any = null
  const showToast = (msg: string = "Copied to clipboard") => {
    setToastMsg(msg)
    if (toastTimer) clearTimeout(toastTimer)
    toastTimer = setTimeout(() => setToastMsg(""), 2200)
  }

  const handleCopy = (): boolean => {
    try {
      const sel = (renderer as any).getSelection?.()
      if (sel) {
        const text = sel.getSelectedText?.()
        if (text && text.trim().length > 0) {
          copyToClipboard(text)
          showToast("Copied to clipboard")
          ;(renderer as any).clearSelection?.()
          return true
        }
      }
    } catch {}
    return false
  }

  // ── Theme State ──
  const [themeName, setThemeName] = createSignal(DEFAULT_THEME)
  const theme = () => resolveTheme(themes[themeName()] || themes["opencode"], "dark")

  // ── Telemetry & System State ──
  const [status, setStatus] = createSignal<SystemStatus>({
    watched_dirs: ["/home/kriteshgoud"],
    files_indexed: 1913,
    files_failed: 0,
    last_indexed_at: null,
  })

  // ── Ollama Models State ──
  const [availableModels, setAvailableModels] = createSignal<OllamaModel[]>([
    { name: "qwen2.5:3b", size: "1.8 GB", parameters: "3.1B", quantization: "Q4_K_M", is_embedding: false },
    { name: "qwen2.5-coder:7b", size: "4.4 GB", parameters: "7.6B", quantization: "Q4_K_M", is_embedding: false },
    { name: "qwen2.5-coder:3b", size: "1.8 GB", parameters: "3.1B", quantization: "Q4_K_M", is_embedding: false },
    { name: "llama3.2:3b", size: "1.9 GB", parameters: "3.2B", quantization: "Q4_K_M", is_embedding: false },
    { name: "llama2:7b-chat", size: "3.6 GB", parameters: "7B", quantization: "Q4_0", is_embedding: false },
  ])
  const [activeModel, setActiveModel] = createSignal("qwen2.5:3b")

  // ── Sources & Preview State (empty by default, populated only when queries match files) ──
  const [sources, setSources] = createSignal<SourceItem[]>([])
  const [selectedSourceIndex, setSelectedSourceIndex] = createSignal(0)

  // ── Command Palette & Mode State ──
  const [showPalette, setShowPalette] = createSignal(false)
  const [paletteCategory, setPaletteCategory] = createSignal<string | undefined>(undefined)
  const [agentMode, setAgentMode] = createSignal("Build")
  const AGENT_MODES = ["Build", "Query", "Shell", "Ask"]

  // ── Slash Commands Menu State ──
  const [slashIndex, setSlashIndex] = createSignal(0)

  // ── Chat Transcript Messages ──
  const [messages, setMessages] = createSignal<MessageItem[]>([])

  // ── Input Prompt & History State ──
  const [inputVal, setInputVal] = createSignal("")
  const [cursorPos, setCursorPos] = createSignal(0)
  const [isProcessing, setIsProcessing] = createSignal(false)
  const [commandHistory, setCommandHistory] = createSignal<string[]>([])
  const [historyIndex, setHistoryIndex] = createSignal(-1)
  const [draftInput, setDraftInput] = createSignal("")

  // Rendered input lines with accurate cursor position (handles multiline and cursor slicing)
  const renderedInputLines = createMemo(() => {
    const val = inputVal()
    const pos = cursorPos()
    if (!val) return ["█ "]

    const lines = val.split("\n")
    let charOffset = 0
    let placed = false
    const result: string[] = []

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i]
      const lineEnd = charOffset + line.length
      if (!placed && pos >= charOffset && (pos <= lineEnd || i === lines.length - 1)) {
        const offset = Math.min(Math.max(0, pos - charOffset), line.length)
        result.push(line.slice(0, offset) + "█" + line.slice(offset))
        placed = true
      } else {
        result.push(line)
      }
      charOffset = lineEnd + 1
    }

    if (!placed) {
      if (result.length > 0) result[result.length - 1] += "█"
      else result.push("█")
    }

    return result
  })

  // Load live status & models & wire up copy-on-select
  onMount(async () => {
    if (renderer && (renderer as any).console) {
      (renderer as any).console.onCopySelection = async (text: string) => {
        if (!text || text.length === 0) return
        copyToClipboard(text)
        showToast("Copied to clipboard")
        renderer.clearSelection?.()
      }
    }

    const [s, m] = await Promise.all([fetchStatus(), fetchModels()])
    setStatus(s)
    if (m && m.length > 0) {
      setAvailableModels(m)
    }
  })

  const exitApp = () => {
    try {
      (renderer as any)?.destroy?.()
    } catch {}
    process.stdout.write(sessionEpilogue({ title: sessionTitle(), sessionID: "ses_" + Date.now().toString(36) }) + "\n")
    process.exit(0)
  }

  // ── Slash Commands Definition ──
  const slashCommands = createMemo<SlashCommand[]>(() => [
    {
      name: "/agents",
      description: "Switch agent (Build, Query, Shell, Ask)",
      action: () => {
        setPaletteCategory("Agent")
        setShowPalette(true)
        setInputVal("")
      },
    },
    {
      name: "/model",
      description: "Switch Ollama LLM model",
      action: () => {
        setPaletteCategory("Model")
        setShowPalette(true)
        setInputVal("")
      },
    },
    {
      name: "/themes",
      description: "Switch color theme",
      action: () => {
        setPaletteCategory("Theme")
        setShowPalette(true)
        setInputVal("")
      },
    },
    {
      name: "/status",
      description: "View indexing health & files",
      action: async () => {
        const s = await fetchStatus()
        setStatus(s)
        const timeStr = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
        setMessages((prev) => [
          ...prev,
          {
            id: String(Date.now()),
            role: "system",
            content: `System Status:\n• Active Model: ${activeModel()}\n• Files Indexed: ${s.files_indexed.toLocaleString()}\n• Failed: ${s.files_failed}\n• Watched Dirs: ${s.watched_dirs.join(", ")}`,
            timestamp: timeStr,
          },
        ])
        setInputVal("")
      },
    },
    {
      name: "/copy",
      description: "Copy transcript to clipboard",
      action: () => {
        const transcript = messages().map((m) => `[${m.role}] ${m.content}`).join("\n\n")
        copyToClipboard(transcript)
        setToastMsg("Transcript copied to clipboard!")
        setTimeout(() => setToastMsg(""), 2000)
        setInputVal("")
      },
    },
    {
      name: "/clear",
      description: "Clear chat messages & reset",
      action: () => {
        setMessages([])
        setSources([])
        setSessionTitle("New Session")
        setInputVal("")
      },
    },
    {
      name: "/debug",
      description: "View system & watcher telemetry",
      action: async () => {
        const s = await fetchStatus()
        setStatus(s)
        const timeStr = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
        setMessages((prev) => [
          ...prev,
          {
            id: String(Date.now()),
            role: "system",
            content: `Debug Telemetry:\n• Model: ${activeModel()}\n• Watched Dirs: ${s.watched_dirs.join(", ")}\n• Files Indexed: ${s.files_indexed}\n• Failed: ${s.files_failed}\n• Last Indexed: ${s.last_indexed_at || "Just now"}`,
            timestamp: timeStr,
          },
        ])
        setInputVal("")
      },
    },
    {
      name: "/help",
      description: "Show available commands & keys",
      action: () => {
        const timeStr = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
        setMessages((prev) => [
          ...prev,
          {
            id: String(Date.now()),
            role: "system",
            content: `Available Commands:\n• /model - Switch Ollama model (${availableModels().filter(m => !m.is_embedding).map(m => m.name).join(", ")})\n• /agents - Switch active agent (Build, Query, Shell, Ask)\n• /themes - Switch theme (/theme nord, tokyonight, matrix, etc.)\n• /status - System health and indexed files\n• /clear - Clear chat messages\n• /copy - Copy transcript to clipboard\n• /exit - Exit RAGA`,
            timestamp: timeStr,
          },
        ])
        setInputVal("")
      },
    },
    {
      name: "/exit",
      description: "Exit the app",
      action: () => {
        exitApp()
      },
    },
  ])

  const filteredSlashCommands = createMemo(() => {
    const q = inputVal().toLowerCase().trim()
    if (!q || !q.startsWith("/")) return []
    if (q === "/") return slashCommands()
    return slashCommands().filter(
      (c) =>
        c.name.toLowerCase().includes(q) ||
        c.description.toLowerCase().includes(q.replace(/^\//, ""))
    )
  })

    // ── Submit Query ──
    const handleSubmit = async () => {
      const text = inputVal().trim()
      if (!text || isProcessing()) return

      // Save to history if not duplicate of previous entry
      setCommandHistory((prev) => {
        if (prev.length > 0 && prev[prev.length - 1] === text) return prev
        return [...prev, text]
      })
      setHistoryIndex(-1)
      setDraftInput("")
      setInputVal("")
      setCursorPos(0)

      const timeStr = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })

    // ── Handle Slash Commands Fallback ──
    if (text.startsWith("/")) {
      const parts = text.split(" ")
      const root = parts[0].toLowerCase()

      if (root === "/model" || root === "/models") {
        if (parts.length > 1) {
          const target = parts[1].toLowerCase()
          const found = availableModels().find(
            (m) => m.name.toLowerCase() === target || m.name.toLowerCase().startsWith(target)
          )
          if (found) {
            setActiveModel(found.name)
            setMessages((prev) => [
              ...prev,
              {
                id: String(Date.now()),
                role: "system",
                content: `Switched active Ollama model to ${found.name} (${found.parameters || found.size})`,
                timestamp: timeStr,
              },
            ])
            return
          }
        }
        setPaletteCategory("Model")
        setShowPalette(true)
        return
      }

      if (root === "/agents" || root === "/agent") {
        setPaletteCategory("Agent")
        setShowPalette(true)
        return
      }

      if (root === "/themes" || root === "/theme" || root === "/them") {
        if (parts.length > 1) {
          const target = parts[1].toLowerCase()
          if (themes[target]) {
            setThemeName(target)
            setMessages((prev) => [
              ...prev,
              {
                id: String(Date.now()),
                role: "system",
                content: `Theme switched to ${target}`,
                timestamp: timeStr,
              }
            ])
            return
          }
        }
        setPaletteCategory("Theme")
        setShowPalette(true)
        return
      }

      const match = slashCommands().find((c) => c.name.toLowerCase() === root)
      if (match) {
        match.action()
        return
      }

      setMessages((prev) => [
        ...prev,
        {
          id: String(Date.now()),
          role: "system",
          content: `Unknown command ${text}. Type /help for commands.`,
          timestamp: timeStr,
        }
      ])
      return
    }

    // Set dynamic session title on first message
    if (sessionTitle() === "New Session") {
      setSessionTitle(text.slice(0, 32))
    }

    // ── 1. Append User Message ──
    const userMsgId = String(Date.now())
    setMessages((prev) => [
      ...prev,
      {
        id: userMsgId,
        role: "user",
        content: text,
        timestamp: timeStr,
      }
    ])

    // ── 2. Add Streaming Assistant Response ──
    const assistantMsgId = String(Date.now() + 1)
    const startTime = Date.now()
    setIsProcessing(true)

    setMessages((prev) => [
      ...prev,
      {
        id: assistantMsgId,
        role: "assistant",
        content: "",
        thoughtTimeMs: 0,
        isThinking: true,
        isStreaming: true,
        timestamp: timeStr,
      }
    ])

    try {
      let accumulatedText = ""

      await executeQueryStream(text, activeModel(), (chunk) => {
        if (chunk.type === "meta") {
          if (chunk.sources && chunk.sources.length > 0) {
            setSources(chunk.sources)
            setSelectedSourceIndex(0)
          } else {
            setSources([])
          }
        } else if (chunk.type === "token" && chunk.token) {
          accumulatedText += chunk.token
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMsgId
                ? {
                    ...msg,
                    content: accumulatedText,
                    isThinking: false,
                    isStreaming: true,
                  }
                : msg
            )
          )
        } else if (chunk.type === "done") {
          const elapsed = chunk.elapsed ? chunk.elapsed * 1000 : Date.now() - startTime
          const elapsedSec = (elapsed / 1000).toFixed(1)
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMsgId
                ? {
                    ...msg,
                    content: accumulatedText,
                    thoughtTimeMs: elapsed,
                    isThinking: false,
                    isStreaming: false,
                    stats: `${activeModel()} (GPU) · ${elapsedSec}s`,
                  }
                : msg
            )
          )
        } else if (chunk.type === "error") {
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMsgId
                ? {
                    ...msg,
                    content: accumulatedText ? `${accumulatedText}\n\n${chunk.error}` : chunk.error || "Unknown error",
                    isThinking: false,
                    isStreaming: false,
                    stats: "Error",
                  }
                : msg
            )
          )
        }
      })
    } catch (err: any) {
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMsgId
            ? {
                ...msg,
                content: `Error running query: ${err.message || String(err)}`,
                isThinking: false,
                isStreaming: false,
                stats: "Error",
              }
            : msg
        )
      )
    } finally {
      setIsProcessing(false)
    }
  }

  // ── Palette Commands List ──
  const paletteCommands = createMemo<PaletteCommand[]>(() => [
    // Agent Modes
    { id: "agent-build", title: "Agent: Build (RAG + Tools)", category: "Agent", action: () => setAgentMode("Build") },
    { id: "agent-query", title: "Agent: Query (Hybrid Search)", category: "Agent", action: () => setAgentMode("Query") },
    { id: "agent-shell", title: "Agent: Shell (OS Commands)", category: "Agent", action: () => setAgentMode("Shell") },
    { id: "agent-ask", title: "Agent: Ask (Fast Direct LLM)", category: "Agent", action: () => setAgentMode("Ask") },
    
    // Dynamic Ollama Models
    ...availableModels()
      .filter((m) => !m.is_embedding)
      .map((m) => ({
        id: `model-${m.name}`,
        title: `Model: ${m.name} (${m.parameters || m.size}${m.name === activeModel() ? " · active" : ""})`,
        category: "Model",
        action: () => {
          setActiveModel(m.name)
          const timeStr = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
          setMessages((prev) => [
            ...prev,
            {
              id: String(Date.now()),
              role: "system",
              content: `Switched active Ollama model to ${m.name} (${m.parameters || m.size})`,
              timestamp: timeStr,
            },
          ])
        },
      })),

    // Themes
    { id: "theme-nord", title: "Theme: Nord", category: "Theme", action: () => setThemeName("nord") },
    { id: "theme-tokyonight", title: "Theme: Tokyo Night", category: "Theme", action: () => setThemeName("tokyonight") },
    { id: "theme-catppuccin", title: "Theme: Catppuccin", category: "Theme", action: () => setThemeName("catppuccin") },
    { id: "theme-dracula", title: "Theme: Dracula", category: "Theme", action: () => setThemeName("dracula") },
    { id: "theme-gruvbox", title: "Theme: Gruvbox", category: "Theme", action: () => setThemeName("gruvbox") },
    { id: "theme-onedark", title: "Theme: One Dark", category: "Theme", action: () => setThemeName("one-dark") },
    { id: "theme-matrix", title: "Theme: Matrix", category: "Theme", action: () => setThemeName("matrix") },
    { id: "theme-opencode", title: "Theme: OpenCode", category: "Theme", action: () => setThemeName("opencode") },
    { id: "theme-rosepine", title: "Theme: Rose Pine", category: "Theme", action: () => setThemeName("rosepine") },
    { id: "theme-solarized", title: "Theme: Solarized", category: "Theme", action: () => setThemeName("solarized") },
    
    // Actions
    { id: "action-clear", title: "Clear Messages / Reset", category: "Action", action: () => {
      setMessages([])
      setSources([])
      setSessionTitle("New Session")
    } },
    {
      id: "action-status",
      title: "View Telemetry & Health",
      category: "Action",
      action: async () => {
        const s = await fetchStatus()
        setStatus(s)
        const timeStr = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
        setMessages((prev) => [
          ...prev,
          {
            id: String(Date.now()),
            role: "system",
            content: `System Status:\n• Active Model: ${activeModel()}\n• Files Indexed: ${s.files_indexed.toLocaleString()}\n• Failed: ${s.files_failed}\n• Watched Dirs: ${s.watched_dirs.join(", ")}`,
            timestamp: timeStr,
          }
        ])
      }
    },
    { id: "action-exit", title: "Exit RAGA", category: "Action", action: () => exitApp() },
  ])

  // ── Keyboard Navigation & Typing ──
  useKeyboard(async (e) => {
    // Ctrl+P: Toggle Command Palette (All categories)
    if (e.ctrl && (e.name === "p" || e.name === "P")) {
      setPaletteCategory(undefined)
      setShowPalette((prev) => !prev)
      return
    }

    if (showPalette()) {
      return
    }

    // Ctrl+C / Ctrl+Shift+C: Copy selection if any, or copy prompt text, else quit
    if (e.ctrl && (e.name === "c" || e.name === "C")) {
      if (handleCopy()) return
      if (inputVal().length > 0) {
        copyToClipboard(inputVal())
        showToast("Copied to clipboard")
        return
      }
      exitApp()
      return
    }

    // Ctrl+V / Ctrl+Shift+V: Paste from clipboard
    if (e.ctrl && (e.name === "v" || e.name === "V")) {
      const clipText = await readFromClipboard()
      if (clipText && clipText.length > 0) {
        const pos = cursorPos()
        const cur = inputVal()
        const updated = cur.slice(0, pos) + clipText + cur.slice(pos)
        setInputVal(updated)
        setCursorPos(pos + clipText.length)
        setSlashIndex(0)
      }
      return
    }

    // Escape handling
    if (e.name === "escape") {
      if (inputVal().startsWith("/")) {
        setInputVal("")
        setCursorPos(0)
        return
      }
      if (isProcessing()) {
        setIsProcessing(false)
        setMessages((prev) => [
          ...prev,
          {
            id: String(Date.now()),
            role: "system",
            content: "Interrupted generation.",
            timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
          }
        ])
        return
      }
      if (historyIndex() !== -1) {
        setHistoryIndex(-1)
        setInputVal(draftInput())
        setCursorPos(draftInput().length)
        return
      }
      return
    }

    // Navigation for Slash Commands
    if (inputVal().startsWith("/") && filteredSlashCommands().length > 0) {
      if (e.name === "up") {
        setSlashIndex((prev) => Math.max(0, prev - 1))
        return
      }
      if (e.name === "down") {
        setSlashIndex((prev) => Math.min(filteredSlashCommands().length - 1, prev + 1))
        return
      }
      if (e.name === "tab" || e.name === "return" || e.name === "enter") {
        const cmd = filteredSlashCommands()[slashIndex()]
        if (cmd) {
          cmd.action()
          return
        }
      }
    }

    // Up Arrow: History backward (previous command)
    if (e.name === "up" && !inputVal().startsWith("/")) {
      const history = commandHistory()
      if (history.length > 0) {
        if (historyIndex() === -1) {
          setDraftInput(inputVal())
          const newIdx = history.length - 1
          setHistoryIndex(newIdx)
          setInputVal(history[newIdx])
          setCursorPos(history[newIdx].length)
        } else if (historyIndex() > 0) {
          const newIdx = historyIndex() - 1
          setHistoryIndex(newIdx)
          setInputVal(history[newIdx])
          setCursorPos(history[newIdx].length)
        }
      }
      return
    }

    // Down Arrow: History forward (next command / draft)
    if (e.name === "down" && !inputVal().startsWith("/")) {
      const history = commandHistory()
      if (historyIndex() !== -1) {
        if (historyIndex() < history.length - 1) {
          const newIdx = historyIndex() + 1
          setHistoryIndex(newIdx)
          setInputVal(history[newIdx])
          setCursorPos(history[newIdx].length)
        } else {
          setHistoryIndex(-1)
          setInputVal(draftInput())
          setCursorPos(draftInput().length)
        }
      }
      return
    }

    // Left Arrow: Move cursor left
    if (e.name === "left") {
      setCursorPos((prev) => Math.max(0, prev - 1))
      return
    }

    // Right Arrow: Move cursor right
    if (e.name === "right") {
      setCursorPos((prev) => Math.min(inputVal().length, prev + 1))
      return
    }

    // Home / Ctrl+A: Move cursor to beginning
    if (e.name === "home" || (e.ctrl && (e.name === "a" || e.name === "A"))) {
      setCursorPos(0)
      return
    }

    // End / Ctrl+E: Move cursor to end
    if (e.name === "end" || (e.ctrl && (e.name === "e" || e.name === "E"))) {
      setCursorPos(inputVal().length)
      return
    }

    // Tab: Cycle Agent Modes (when not in slash menu)
    if (e.name === "tab") {
      const curIdx = AGENT_MODES.indexOf(agentMode())
      const nextIdx = (curIdx + 1) % AGENT_MODES.length
      setAgentMode(AGENT_MODES[nextIdx])
      return
    }

    // Ctrl+L: Clear Chat
    if (e.ctrl && (e.name === "l" || e.name === "L")) {
      setMessages([])
      setSources([])
      setSessionTitle("New Session")
      return
    }

    // Quick Preview: 1-5 keys when in session view and input is empty
    if (!e.ctrl && !e.meta && inputVal() === "" && messages().length > 0 && ["1", "2", "3", "4", "5"].includes(e.name)) {
      const idx = parseInt(e.name) - 1
      if (idx < sources().length) {
        setSelectedSourceIndex(idx)
        return
      }
    }

    // Shift+Enter / Alt+Enter / LineFeed: Insert newline for multiline prompt
    if (
      (e.shift && (e.name === "return" || e.name === "enter")) ||
      e.name === "linefeed" ||
      ((e.ctrl || e.option) && (e.name === "return" || e.name === "enter"))
    ) {
      const pos = cursorPos()
      const cur = inputVal()
      const updated = cur.slice(0, pos) + "\n" + cur.slice(pos)
      setInputVal(updated)
      setCursorPos(pos + 1)
      setSlashIndex(0)
      return
    }

    // Standard Enter: Submit
    if (e.name === "return" || e.name === "enter") {
      handleSubmit()
      return
    }

    // Delete key (delete character ahead of cursor)
    if (e.name === "delete") {
      const pos = cursorPos()
      const cur = inputVal()
      if (pos < cur.length) {
        const updated = cur.slice(0, pos) + cur.slice(pos + 1)
        setInputVal(updated)
      }
      return
    }

    // Backspace: Delete character behind cursor
    if (e.name === "backspace") {
      const pos = cursorPos()
      const cur = inputVal()
      if (pos > 0) {
        const updated = cur.slice(0, pos - 1) + cur.slice(pos)
        setInputVal(updated)
        setCursorPos(pos - 1)
        setSlashIndex(0)
      }
      return
    }

    // Space key
    if (e.name === "space") {
      const pos = cursorPos()
      const cur = inputVal()
      const updated = cur.slice(0, pos) + " " + cur.slice(pos)
      setInputVal(updated)
      setCursorPos(pos + 1)
      setSlashIndex(0)
      return
    }

    // Terminal paste / multi-character input
    if (e.raw && e.raw.length > 1 && !e.ctrl && !e.meta) {
      const pos = cursorPos()
      const cur = inputVal()
      const updated = cur.slice(0, pos) + e.raw + cur.slice(pos)
      setInputVal(updated)
      setCursorPos(pos + e.raw.length)
      setSlashIndex(0)
      return
    }

    // Standard single character
    if (e.raw && e.raw.length === 1 && !e.ctrl && !e.meta) {
      const pos = cursorPos()
      const cur = inputVal()
      const updated = cur.slice(0, pos) + e.raw + cur.slice(pos)
      setInputVal(updated)
      setCursorPos(pos + 1)
      setSlashIndex(0)
    }
  })

  const isHome = () => messages().length === 0

  return (
    <box
      width={dimensions().width}
      height={dimensions().height}
      flexDirection="column"
      backgroundColor={theme().background}
      onMouseUp={() => {
        handleCopy()
      }}
    >
      {/* ── Copied to Clipboard Toast Notification ── */}
      <Show when={toastMsg()}>
        <box
          position="absolute"
          top={1}
          right={2}
          borderStyle="single"
          borderColor={theme().borderActive || theme().primary}
          backgroundColor={theme().backgroundPanel || theme().background}
          paddingLeft={2}
          paddingRight={2}
          paddingTop={0}
          paddingBottom={0}
        >
          <text fg={theme().text}>{toastMsg()}</text>
        </box>
      </Show>

      {/* ── Command Palette Modal ── */}
      <Show when={showPalette()}>
        <CommandPalette
          theme={theme()}
          commands={paletteCommands()}
          category={paletteCategory()}
          onClose={() => setShowPalette(false)}
        />
      </Show>

      <Show
        when={!isHome()}
        fallback={
          /* ── OpenCode Centered Home Screen ── */
          <box
            flexGrow={1}
            flexDirection="column"
            alignItems="center"
            justifyContent="space-between"
            paddingLeft={2}
            paddingRight={2}
          >
            <box flexGrow={1} minHeight={0} />

            {/* Pixel Logo */}
            <box flexShrink={0} marginBottom={2}>
              <Logo theme={theme()} />
            </box>

            {/* Centered Elevated Input Box with floating Slash Menu */}
            <box width="100%" maxWidth={72} flexDirection="column" flexShrink={0}>
              <Show when={inputVal().startsWith("/") && filteredSlashCommands().length > 0}>
                <box width="100%" marginBottom={1}>
                  <SlashMenu
                    theme={theme()}
                    query={inputVal()}
                    selectedIndex={slashIndex()}
                    commands={filteredSlashCommands()}
                    onSelect={(cmd) => cmd.action()}
                    onHover={(idx) => setSlashIndex(idx)}
                  />
                </box>
              </Show>

              <box
                backgroundColor={theme().backgroundPanel}
                paddingLeft={2}
                paddingRight={2}
                paddingTop={1}
                paddingBottom={1}
                flexDirection="column"
              >
                <box flexDirection="row">
                  <text fg={theme().primary}><b>│ </b></text>
                  <Show
                    when={inputVal().length > 0}
                    fallback={
                      <box flexDirection="row">
                        <text fg={theme().text}>█ </text>
                        <text fg={theme().textMuted}>
                          Ask anything... "Search codebase & documents"
                        </text>
                      </box>
                    }
                  >
                    <box flexDirection="column">
                      <For each={renderedInputLines()}>
                        {(line) => <text fg={theme().text}>{line}</text>}
                      </For>
                    </box>
                  </Show>
                </box>

                <box paddingTop={1} flexDirection="row" gap={2}>
                  <text fg={theme().textMuted}>
                    <span style={{ fg: theme().primary }}>{agentMode()}</span> · {activeModel()} (GPU) nomic-embed-text · <span style={{ fg: theme().warning }}>high</span>
                  </text>
                </box>
              </box>

              {/* Input Keybind Hints */}
              <box flexDirection="row" justifyContent="flex-end" paddingTop={1}>
                <text fg={theme().textMuted}>
                  <span style={{ fg: theme().text }}>tab</span> agents  <span style={{ fg: theme().text }}>ctrl+p</span> commands
                </text>
              </box>

              {/* Tips Banner */}
              <box paddingTop={2} flexDirection="row" gap={1} justifyContent="center" alignItems="center">
                <text fg={theme().warning}>● <b>Tip</b></text>
                <text fg={theme().textMuted}>Add files to watched folders for semantic RAG search</text>
              </box>
            </box>

            <box flexGrow={1} minHeight={0} />

            {/* Bottom Footer Bar */}
            <box width="100%" flexDirection="row" justifyContent="space-between" paddingBottom={1}>
              <text fg={theme().textMuted}>~</text>
              <text fg={theme().textMuted}>1.0.0</text>
            </box>
          </box>
        }
      >
        {/* ── OpenCode 2-Column Session Screen ── */}
        <box flexGrow={1} minHeight={0} flexDirection="row">
          {/* Left Column: Chat History & Input */}
          <box flexGrow={1} flexDirection="column" paddingRight={1}>
            <scrollbox
              flexGrow={1}
              paddingLeft={1}
              paddingRight={2}
              paddingTop={1}
              verticalScrollbarOptions={{
                trackOptions: {
                  backgroundColor: theme().background,
                  foregroundColor: theme().borderActive,
                },
              }}
            >
              <For each={messages()}>
                {(msg) => <MessageCard message={msg} theme={theme()} />}
              </For>
            </scrollbox>

            {/* Elevated Input Prompt */}
            <box flexDirection="column" paddingLeft={1} paddingRight={2} paddingBottom={1} flexShrink={0}>
              <Show when={inputVal().startsWith("/") && filteredSlashCommands().length > 0}>
                <box width="100%" marginBottom={1}>
                  <SlashMenu
                    theme={theme()}
                    query={inputVal()}
                    selectedIndex={slashIndex()}
                    commands={filteredSlashCommands()}
                    onSelect={(cmd) => cmd.action()}
                    onHover={(idx) => setSlashIndex(idx)}
                  />
                </box>
              </Show>

              <box
                backgroundColor={theme().backgroundPanel}
                paddingLeft={2}
                paddingRight={2}
                paddingTop={1}
                paddingBottom={1}
                flexDirection="column"
              >
                <box flexDirection="row">
                  <text fg={theme().primary}><b>│ </b></text>
                  <Show
                    when={inputVal().length > 0}
                    fallback={
                      <box flexDirection="row">
                        <text fg={theme().text}>█ </text>
                        <text fg={theme().textMuted}>
                          Ask anything or type /themes, /model, /status...
                        </text>
                      </box>
                    }
                  >
                    <box flexDirection="column">
                      <For each={renderedInputLines()}>
                        {(line) => <text fg={theme().text}>{line}</text>}
                      </For>
                    </box>
                  </Show>
                </box>

                <box paddingTop={1} flexDirection="row" gap={2}>
                  <text fg={theme().textMuted}>
                    <span style={{ fg: theme().primary }}>{agentMode()}</span> · {activeModel()} (GPU) nomic-embed-text · <span style={{ fg: theme().warning }}>high</span>
                  </text>
                </box>
              </box>

              {/* Bottom Statusline */}
              <box flexDirection="row" justifyContent="space-between" paddingTop={1}>
                <Show
                  when={isProcessing()}
                  fallback={
                    <text fg={theme().textMuted}>/home/kriteshgoud</text>
                  }
                >
                  <box flexDirection="row" gap={1} alignItems="center">
                    <ThinkingScanner theme={theme()} active={isProcessing()} />
                    <text fg={theme().textMuted}>
                      <span style={{ fg: theme().text }}>esc</span> interrupt
                    </text>
                  </box>
                </Show>

                <box flexDirection="row" gap={2} alignItems="center">
                  <text fg={theme().textMuted}>{status().files_indexed.toLocaleString()} files</text>
                  <text fg={theme().text}>
                    <span style={{ fg: theme().text }}>ctrl+p</span> <span style={{ fg: theme().textMuted }}>commands</span>
                  </text>
                </box>
              </box>
            </box>
          </box>

          {/* Right Column: Custom Sources & Chunk Preview Sidebar */}
          <Sidebar
            theme={theme()}
            title={sessionTitle()}
            modelName={activeModel()}
            agentMode={agentMode()}
            sources={sources()}
            selectedIndex={selectedSourceIndex()}
            fileCount={status().files_indexed}
            onSelect={(idx) => setSelectedSourceIndex(idx)}
          />
        </box>
      </Show>
    </box>
  )
}
