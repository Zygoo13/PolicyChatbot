import { useState } from "react";
import "./index.css";

function App() {
  const [question, setQuestion] = useState("");
  const [mode, setMode] = useState("llm_only");
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        "Xin chào, mình là chatbot hỗ trợ policy quản lý dự án phần mềm. Bạn muốn hỏi gì?",
      mode: "llm_only",
      sources: [],
    },
  ]);

  const handleSend = async () => {
    const trimmed = question.trim();
    if (!trimmed || loading) return;

    setMessages((prev) => [
      ...prev,
      { role: "user", content: trimmed },
    ]);
    setQuestion("");
    setLoading(true);

    try {
      const response = await fetch("http://127.0.0.1:8000/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          question: trimmed,
          mode: mode,
        }),
      });

      const data = await response.json();

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: data.answer || "Không nhận được phản hồi từ backend.",
          mode: data.mode || mode,
          sources: data.sources || [],
        },
      ]);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "Không thể kết nối backend.",
          mode: mode,
          sources: [],
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">
      <div className="chat-container">
        <h1 className="title">Policy Chatbot MVP</h1>

        <div className="input-area" style={{ marginBottom: "12px" }}>
          <select
            value={mode}
            onChange={(e) => setMode(e.target.value)}
            disabled={loading}
          >
            <option value="llm_only">llm_only</option>
            <option value="rag">rag</option>
            <option value="rag_prompt">rag_prompt</option>
          </select>
        </div>

        <div className="chat-box">
          {messages.map((msg, index) => (
            <div
              key={index}
              className={`message ${msg.role === "user" ? "user" : "assistant"}`}
            >
              <strong>{msg.role === "user" ? "Bạn" : "Bot"}:</strong>{" "}
              <div style={{ whiteSpace: "pre-wrap", display: "inline" }}>
                {msg.content}
              </div>

              {msg.role === "assistant" && msg.mode && (
                <div style={{ marginTop: "8px", fontSize: "13px", opacity: 0.8 }}>
                  <div>
                    <strong>Mode:</strong> {msg.mode}
                  </div>

                  {msg.sources && msg.sources.length > 0 && (
                    <div style={{ marginTop: "4px" }}>
                      <strong>Sources:</strong>
                      <ul style={{ margin: "4px 0 0 18px" }}>
                        {msg.sources.map((src, i) => (
                          <li key={i}>
                            {src.file_name}
                            {src.chunk_id ? ` - ${src.chunk_id}` : ""}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}

          {loading && (
            <div className="message assistant">
              <strong>Bot:</strong> Đang suy nghĩ...
            </div>
          )}
        </div>

        <div className="input-area">
          <input
            type="text"
            placeholder="Nhập câu hỏi của bạn..."
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                handleSend();
              }
            }}
            disabled={loading}
          />

          <button onClick={handleSend} disabled={loading}>
            {loading ? "..." : "Gửi"}
          </button>
        </div>
      </div>
    </div>
  );
}

export default App;