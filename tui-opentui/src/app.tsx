import { createSignal, onMount, For, Show } from "solid-js"
import { useTerminalDimensions, useRenderer, useKeyboard } from "@opentui/solid"
import { RGBA } from "@opentui/core"
import { resolveTheme, allThemes, type Theme } from "./theme"
import { Header } from "./components/header"
import { Sidebar, type SourceItem } from "./components/sidebar"
import { MessageCard, type MessageItem } from "./components/message"
import { fetchStatus, executeQuery, type SystemStatus } from "./bridge"
import { copyToClipboard } from "./util/clipboard"

const DEFAULT_THEME = "opencode"

export function App() {
  const dimensions = useTerminalDimensions()
  const renderer = useRenderer()
  const themes = allThemes()

  // ── Toast / Clipboard State ──
  const [toastMsg, setToastMsg] = createSignal("")

  const handleCopy = (): boolean => {
    try {
      const sel = (renderer as any).getSelection?.()
      if (sel) {
        const text = sel.getSelectedText?.()
        if (text && text.trim().length > 0) {
          copyToClipboard(text)
          setToastMsg("Copied to clipboard!")
          setTimeout(() => setToastMsg(""), 2000)
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

  // ── Sources & Preview State ──
  const [sources, setSources] = createSignal<SourceItem[]>([
    {
      id: 1,
      path: "/home/kriteshgoud/Documents/NMIMS/projects/RAGA/core/retriever.py",
      score: 0.94,
      chunkText: "def retrieve(query: str, top_k: int = 7) -> list[dict]:\n    # Hybrid search: vector similarity + BM25 keyword matching + cross-encoder rerank\n    candidate_chunks = vector_store.search(query, k=top_k * 3)\n    return reranker.rerank(query, candidate_chunks)[:top_k]"
    },
    {
      id: 2,
      path: "/home/kriteshgoud/Documents/NMIMS/projects/RAGA/core/generator.py",
      score: 0.88,
      chunkText: "def generate_answer(query: str, chunks: list[dict]) -> str:\n    prompt = build_rag_prompt(query, chunks)\n    return ollama_client.generate(model='qwen2.5:3b', prompt=prompt)"
    },
    {
      id: 3,
      path: "/home/kriteshgoud/Documents/NMIMS/projects/RAGA/storage/vector_store.py",
      score: 0.76,
      chunkText: "class VectorStore:\n    def __init__(self, db_path: str):\n        self.client = chromadb.PersistentClient(path=db_path)\n        self.collection = self.client.get_or_create_collection('raga_docs')"
    }
  ])
  const [selectedSourceIndex, setSelectedSourceIndex] = createSignal(0)

  // ── Chat Transcript Messages ──
  const [messages, setMessages] = createSignal<MessageItem[]>([
    {
      id: "sys-1",
      role: "system",
      content: "◈ Welcome to RAGA OpenTUI — Local Document Intelligence built with OpenTUI and SolidJS.\nType a query below to retrieve documents, or use `/themes`, `/status`, `/help`.",
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    }
  ])

  // ── Input Prompt State ──
  const [inputVal, setInputVal] = createSignal("")
  const [isProcessing, setIsProcessing] = createSignal(false)

  // Load live status & wire up copy-on-select
  onMount(async () => {
    if (renderer && (renderer as any).console) {
      (renderer as any).console.onCopySelection = async (text: string) => {
        if (!text || text.length === 0) return
        copyToClipboard(text)
        setToastMsg("Copied to clipboard!")
        setTimeout(() => setToastMsg(""), 2000)
        renderer.clearSelection?.()
      }
    }

    const s = await fetchStatus()
    setStatus(s)
  })

  // ── Submit Query or Slash Command ──
  const handleSubmit = async () => {
    const text = inputVal().trim()
    if (!text || isProcessing()) return
    setInputVal("")

    const timeStr = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })

    // ── Handle Slash Commands ──
    if (text.startsWith("/")) {
      const parts = text.split(" ")
      const root = parts[0].toLowerCase()

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
                content: `🎨 Theme switched to **${target}**`,
                timestamp: timeStr,
              }
            ])
            return
          }
        }
        const available = Object.keys(themes).slice(0, 16).join(", ")
        setMessages((prev) => [
          ...prev,
          {
            id: String(Date.now()),
            role: "system",
            content: `**Available themes:** \`${available}\`\n\nUsage: \`/theme nord\`, \`/theme tokyonight\`, \`/theme catppuccin\`, \`/theme matrix\`, etc.`,
            timestamp: timeStr,
          }
        ])
        return
      }

      if (root === "/clear") {
        setMessages([])
        return
      }

      if (root === "/status") {
        const s = await fetchStatus()
        setStatus(s)
        setMessages((prev) => [
          ...prev,
          {
            id: String(Date.now()),
            role: "system",
            content: `### System Telemetry & Health\n- **Files Indexed:** \`${s.files_indexed.toLocaleString()}\`\n- **Failed Files:** \`${s.files_failed}\`\n- **Watched Dirs:** \`${s.watched_dirs.join(", ")}\``,
            timestamp: timeStr,
          }
        ])
        return
      }

      if (root === "/help") {
        setMessages((prev) => [
          ...prev,
          {
            id: String(Date.now()),
            role: "system",
            content: `### RAGA OpenTUI Keybindings & Commands\n\n` +
              `| Key / Command | Description |\n` +
              `| :--- | :--- |\n` +
              `| \`Enter\` | Submit query or slash command |\n` +
              `| \`1\` – \`5\` | Quick Preview source 1 through 5 |\n` +
              `| \`/themes <name>\` | Switch themes (nord, tokyonight, catppuccin, matrix...) |\n` +
              `| \`/status\` | View daemon indexing telemetry |\n` +
              `| \`/clear\` | Clear chat messages |\n` +
              `| \`Ctrl + L\` | Clear chat history |\n` +
              `| \`Ctrl + C\` | Exit RAGA |`,
            timestamp: timeStr,
          }
        ])
        return
      }

      if (root === "/exit") {
        process.exit(0)
      }

      setMessages((prev) => [
        ...prev,
        {
          id: String(Date.now()),
          role: "system",
          content: `Unknown command \`${text}\`. Type \`/help\` for available commands.`,
          timestamp: timeStr,
        }
      ])
      return
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

    // ── 2. Append Assistant Thinking Message ──
    const asstMsgId = String(Date.now() + 1)
    setIsProcessing(true)
    setMessages((prev) => [
      ...prev,
      {
        id: asstMsgId,
        role: "assistant",
        content: "Synthesizing answer from candidate files...",
        thinking: "Searching hybrid vector index & reranking candidate chunks...",
        isStreaming: true,
        timestamp: timeStr,
      }
    ])

    // ── 3. Execute Query via Python Engine ──
    try {
      const result = await executeQuery(text)

      // Update right sidebar sources
      if (result.sources && result.sources.length > 0) {
        setSources(result.sources)
        setSelectedSourceIndex(0)
      }

      // Update assistant message with finalized answer
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === asstMsgId
            ? {
                ...msg,
                content: result.text || "No response generated.",
                thinking: `Retrieved ${result.sources?.length || 0} chunks (${result.elapsed}s)`,
                isStreaming: false,
                stats: `⚡ ${result.elapsed}s · ${result.sources?.length || 0} sources reranked · Qwen 2.5 3B (GPU)`,
              }
            : msg
        )
      )
    } catch (err) {
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === asstMsgId
            ? {
                ...msg,
                content: `Error retrieving response: ${err}`,
                thinking: undefined,
                isStreaming: false,
              }
            : msg
        )
      )
    } finally {
      setIsProcessing(false)
    }
  }

  // ── Keyboard Navigation & Typing ──
  useKeyboard((e) => {
    // Ctrl+C: Copy selection if any, else quit
    if (e.ctrl && (e.name === "c" || e.name === "C")) {
      if (handleCopy()) return
      process.exit(0)
    }

    // Ctrl+L: Clear Chat
    if (e.ctrl && (e.name === "l" || e.name === "L")) {
      setMessages([])
      return
    }

    // Quick Preview: 1-5 keys when input is empty
    if (!e.ctrl && inputVal() === "" && ["1", "2", "3", "4", "5"].includes(e.name)) {
      const idx = parseInt(e.name) - 1
      if (idx < sources().length) {
        setSelectedSourceIndex(idx)
        return
      }
    }

    // Enter / Return: Submit
    if (e.name === "return" || e.name === "enter") {
      handleSubmit()
      return
    }

    // Backspace: Delete character
    if (e.name === "backspace") {
      setInputVal((prev) => prev.slice(0, -1))
      return
    }

    // Space key
    if (e.name === "space") {
      setInputVal((prev) => prev + " ")
      return
    }

    // Standard characters
    if (e.raw && e.raw.length === 1 && !e.ctrl) {
      setInputVal((prev) => prev + e.raw)
    }
  })

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
      {/* ── 1. Top Header Session Bar ── */}
      <Header
        theme={theme()}
        fileCount={status().files_indexed}
        modelName="qwen2.5:3b (GPU)"
        toastMsg={toastMsg()}
      />

      {/* ── 2. Main 2-Column Body ── */}
      <box flexGrow={1} minHeight={0} flexDirection="row">
        {/* ── Left Column: Chat History & Input ── */}
        <box flexGrow={1} flexDirection="column" paddingRight={1}>
          {/* Scrollable Chat Transcript */}
          <scrollbox
            flexGrow={1}
            paddingLeft={2}
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
          <box flexDirection="column" paddingLeft={2} paddingRight={2} paddingBottom={1} flexShrink={0}>
            <box
              backgroundColor={theme().backgroundPanel}
              borderLeftColor={theme().primary}
              paddingLeft={2}
              paddingRight={2}
              paddingTop={1}
              paddingBottom={1}
              flexDirection="column"
            >
              <box flexDirection="row" gap={1}>
                <text fg={theme().primary}><b>│</b></text>
                <Show
                  when={inputVal().length > 0}
                  fallback={
                    <text fg={theme().textMuted}>
                      Ask about documents, mention @file, or type /themes, /status, /help...
                    </text>
                  }
                >
                  <text fg={theme().text}>{inputVal()}</text>
                </Show>
                <text fg={theme().primary}>█</text>
              </box>

              <box paddingTop={1} flexDirection="row" gap={2}>
                <text fg={theme().textMuted}>
                  <span style={{ fg: theme().primary }}><b>Query</b></span> · Qwen 2.5 3B (GPU) · nomic-embed-text · <span style={{ fg: theme().warning }}>hybrid RAG</span>
                </text>
              </box>
            </box>

            <box flexDirection="row" justifyContent="space-between" paddingTop={1}>
              <text fg={theme().textMuted}>~/Documents/NMIMS/projects/RAGA</text>
              <text fg={theme().textMuted}>
                <span style={{ fg: theme().text }}>Enter</span> submit · <span style={{ fg: theme().text }}>1-5</span> preview · <span style={{ fg: theme().text }}>ctrl+c</span> quit
              </text>
            </box>
          </box>
        </box>

        {/* ── Right Column: Custom Sources & Chunk Preview Sidebar ── */}
        <Sidebar
          theme={theme()}
          sources={sources()}
          selectedIndex={selectedSourceIndex()}
          onSelect={(idx) => setSelectedSourceIndex(idx)}
        />
      </box>
    </box>
  )
}
