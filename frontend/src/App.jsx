import { useMemo, useRef, useState, useEffect } from "react";
import "./index.css";


const API_BASE_URL = "http://127.0.0.1:8000";

const MODE_OPTIONS = [
  {
    value: "llm_only",
    label: "LLM Only",
    description: "Model trả lời trực tiếp, không dùng policy context",
    accent: "neutral",
  },
  {
    value: "rag",
    label: "RAG",
    description: "Truy xuất context từ policy trước khi trả lời",
    accent: "blue",
  },
  {
    value: "rag_prompt",
    label: "RAG Prompt",
    description: "RAG + format câu trả lời chuẩn để demo đẹp hơn",
    accent: "violet",
  },
];

const INITIAL_MESSAGES = [
  {
    id: crypto.randomUUID(),
    role: "assistant",
    content:
      "Xin chào, mình là chatbot hỗ trợ policy quản lý dự án phần mềm. Bạn muốn hỏi gì?",
    mode: "rag_prompt",
    sources: [],
  },
];

function formatSourceLabel(source) {
  const title = source?.title?.trim();
  const section = source?.section?.trim();

  if (title && section) return `${title} · ${section}`;
  if (section) return section;
  if (title) return title;
  if (source?.file_name) return source.file_name;
  return "Unknown source";
}

function SourceCard({ source, index }) {
  return (
    <div className="source-card">
      <div className="source-card-top">
        <span className="source-index">#{index + 1}</span>
        <span className="source-title">{formatSourceLabel(source)}</span>
      </div>

      <div className="source-meta">
        <span>{source.file_name || "unknown file"}</span>
        {source.distance !== undefined && source.distance !== null ? (
          <span>score {source.distance.toFixed(3)}</span>
        ) : null}
      </div>

      {source.content_preview ? (
        <div className="source-preview">{source.content_preview}</div>
      ) : null}
    </div>
  );
}

function SourcesPanel({ sources }) {
  if (!sources?.length) return null;

  return (
    <div className="sources-panel">
      <div className="sources-header">
        <span className="sources-dot" />
        <span>Nguồn tham chiếu</span>
      </div>

      <div className="sources-grid">
        {sources.map((source, index) => (
          <SourceCard
            key={`${source.chunk_id || source.file_name || "source"}-${index}`}
            source={source}
            index={index}
          />
        ))}
      </div>
    </div>
  );
}

function Message({ message }) {
  const isUser = message.role === "user";

  return (
    <div className={`message-row ${isUser ? "user" : "assistant"}`}>
      <div className={`message-shell ${isUser ? "user" : "assistant"}`}>
        <div className="message-head">
          <div className="message-avatar">{isUser ? "B" : "AI"}</div>
          <div className="message-meta">
            <div className="message-author">{isUser ? "Bạn" : "Policy Bot"}</div>
            {!isUser && message.mode ? (
              <div className="message-mode">{message.mode}</div>
            ) : null}
          </div>
        </div>

        <div className="message-body">{message.content}</div>

        {!isUser ? <SourcesPanel sources={message.sources.slice(0, 2)} /> : null}
      </div>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="empty-state">
      <div className="empty-orb empty-orb-1" />
      <div className="empty-orb empty-orb-2" />
      <div className="empty-card">
        <div className="empty-badge">Demo ready</div>
        <h3>Hỏi policy theo ngôn ngữ tự nhiên</h3>
        <p>
          Ví dụ:
          <br />
          “Definition of Done gồm những tiêu chí nào?”
          <br />
          “Incident Response khác Incident Resolution ở đâu?”
          <br />
          “Change Request Submission gồm những bước nào?”
        </p>
      </div>
    </div>
  );
}

function App() {
  const [question, setQuestion] = useState("");
  const [mode, setMode] = useState("rag_prompt");
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState(INITIAL_MESSAGES);
  const [error, setError] = useState("");
  const textareaRef = useRef(null);
  const chatEndRef = useRef(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const currentMode = useMemo(
    () => MODE_OPTIONS.find((item) => item.value === mode) ?? MODE_OPTIONS[2],
    [mode]
  );

  const autoResize = () => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "0px";
    el.style.height = `${Math.min(el.scrollHeight, 220)}px`;
  };

  const handleChangeQuestion = (event) => {
    setQuestion(event.target.value);
    requestAnimationFrame(autoResize);
  };

  const handleSend = async () => {
    const trimmed = question.trim();
    if (!trimmed || loading) return;

    setError("");

    const userMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: trimmed,
      mode: null,
      sources: [],
    };

    setMessages((prev) => [...prev, userMessage]);
    setQuestion("");

    if (textareaRef.current) {
      textareaRef.current.style.height = "120px";
    }

    setLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          question: trimmed,
          mode,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Không thể xử lý yêu cầu.");
      }

      const assistantMessage = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: data.answer || "Không nhận được phản hồi từ backend.",
        mode: data.mode || mode,
        sources: data.sources || [],
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Không thể kết nối backend.";

      setError(message);

      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: `Lỗi: ${message}`,
          mode,
          sources: [],
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      handleSend();
    }
  };

  const handleClear = () => {
    if (loading) return;
    setMessages(INITIAL_MESSAGES);
    setQuestion("");
    setError("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "120px";
    }
  };

  return (
    <div className="page">
      <div className="page-gradient page-gradient-1" />
      <div className="page-gradient page-gradient-2" />

      <main className="app-frame">
        <section className="hero-card">
          <div className="hero-left">
            <div className="hero-pill">Policy Assistant</div>
            <h1>Policy Chatbot</h1>
            <p>
              Chatbot tư vấn policy quản lý dự án phần mềm với chế độ LLM, RAG,
              và RAG Prompt để so sánh kết quả rõ ràng hơn.
            </p>

            <div className="hero-stats">
              <div className="stat-card">
                <span className="stat-label">Backend</span>
                <span className="stat-value online">Online</span>
              </div>
              <div className="stat-card">
                <span className="stat-label">Endpoint</span>
                <span className="stat-value small">{API_BASE_URL}</span>
              </div>
            </div>
          </div>

          <div className="hero-right">
            <button className="ghost-button" onClick={handleClear} disabled={loading}>
              Xóa chat
            </button>
          </div>
        </section>

        <section className="control-card">
          <div className="control-top">
            <div>
              <div className="section-label">Chế độ trả lời</div>
              <div className="section-title">Response mode</div>
            </div>
          </div>

          <div className="mode-grid">
            {MODE_OPTIONS.map((option) => (
              <button
                key={option.value}
                type="button"
                className={`mode-card ${mode === option.value ? "active" : ""} ${option.accent}`}
                onClick={() => setMode(option.value)}
                disabled={loading}
              >
                <div className="mode-card-head">
                  <div className="mode-radio">{mode === option.value ? "●" : "○"}</div>
                  <div className="mode-name">{option.label}</div>
                </div>
                <div className="mode-desc">{option.description}</div>
              </button>
            ))}
          </div>

          <div className="mode-banner">
            <span className={`mode-tag ${currentMode.accent}`}>{currentMode.label}</span>
            <span className="mode-banner-text">{currentMode.description}</span>
          </div>
        </section>

        <section className="chat-card">
          <div className="chat-card-head">
            <div>
              <div className="section-label">Conversation</div>
              <div className="section-title">Chat workspace</div>
            </div>

            <div className="chat-status">
              <span className="status-ping" />
              <span>{loading ? "Đang trả lời..." : "Sẵn sàng"}</span>
            </div>
          </div>

          <div className="chat-scroll">
            {messages.length <= 1 ? <EmptyState /> : null}

            {messages.map((message) => (
              <Message key={message.id} message={message} />
            ))}

            {loading ? (
              <div className="message-row assistant">
                <div className="message-shell assistant loading-shell">
                  <div className="message-head">
                    <div className="message-avatar">AI</div>
                    <div className="message-meta">
                      <div className="message-author">Policy Bot</div>
                      <div className="message-mode">thinking</div>
                    </div>
                  </div>

                  <div className="typing-line">
                    <span />
                    <span />
                    <span />
                  </div>
                </div>
              </div>
            ) : null}
            <div ref={chatEndRef} />
          </div>
        </section>

        <section className="composer-card">
          <div className="composer-top">
            <div>
              <div className="section-label">Nhập câu hỏi</div>
              <div className="section-title">Ask the bot</div>
            </div>
          </div>

          <div className="composer-box">
            <textarea
              ref={textareaRef}
              value={question}
              onChange={handleChangeQuestion}
              onKeyDown={handleKeyDown}
              placeholder="Ví dụ: Definition of Done gồm những tiêu chí nào?"
              disabled={loading}
              rows={4}
            />

            <div className="composer-actions">
              <div className="composer-hint">
                Enter để gửi · Shift + Enter để xuống dòng
              </div>

              <button
                className="send-button"
                onClick={handleSend}
                disabled={loading || !question.trim()}
              >
                {loading ? "Đang gửi..." : "Gửi câu hỏi"}
              </button>
            </div>
          </div>

          {error ? <div className="error-box">{error}</div> : null}
        </section>
      </main>
    </div>
  );
}

export default App;