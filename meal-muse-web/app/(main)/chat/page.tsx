"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, Send, Bot, User, RefreshCw } from "lucide-react";
import api from "@/lib/api";
import { toast } from "@/components/ui/toast";

interface Message {
  id?: string;
  role: "user" | "assistant";
  content: string;
  session_id?: string;
  actions?: Array<{ type: string; data: string }>;
}

interface Session {
  session_id: string;
  last_message_at: string;
  message_count: number;
}

const quickQuestions = [
  "今天饮食怎么样？",
  "备孕应该多吃什么？",
  "最近营养够吗？",
  "经期适合吃什么？",
];

export default function ChatPage() {
  const router = useRouter();
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content:
        "你好！我是你的 AI 饮食健康助手 🌿\n\n我会根据你的饮食记录，为你提供个性化的健康建议。你可以问我：\n• 今天的饮食是否合理\n• 备孕/经期饮食建议\n• 想吃什么类型的菜\n• 任何健康饮食问题\n\n有什么想问的吗？",
    },
  ]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [sessionId, setSessionId] = useState<string | undefined>(undefined);

  // 对话历史状态
  const [showHistory, setShowHistory] = useState(false);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loadingSessions, setLoadingSessions] = useState(false);

  // 加载会话列表
  const fetchSessions = useCallback(async () => {
    setLoadingSessions(true);
    try {
      const res = await api.get("/chat/sessions");
      setSessions(res.data.sessions ?? []);
    } catch {
      // 静默失败，不影响主流程
    } finally {
      setLoadingSessions(false);
    }
  }, []);

  // 展开历史面板时拉取列表
  useEffect(() => {
    if (showHistory) {
      fetchSessions();
    }
  }, [showHistory, fetchSessions]);

  // 加载指定会话的消息
  const loadSession = async (sid: string) => {
    try {
      const res = await api.get(`/chat/sessions/${sid}/messages`);
      const msgs: Message[] = (res.data.messages ?? []).map(
        (m: { id: string; role: "user" | "assistant"; content: string; session_id: string }) => ({
          id: m.id,
          role: m.role,
          content: m.content,
          session_id: m.session_id,
        })
      );
      if (msgs.length > 0) {
        setMessages(msgs);
        setSessionId(sid);
      }
    } catch {
      // 静默失败
    }
    setShowHistory(false);
  };

  // 新建对话
  const handleNewChat = () => {
    setSessionId(undefined);
    setMessages([
      {
        role: "assistant",
        content:
          "你好！我是你的 AI 饮食健康助手 🌿\n\n我会根据你的饮食记录，为你提供个性化的健康建议。你可以问我：\n• 今天的饮食是否合理\n• 备孕/经期饮食建议\n• 想吃什么类型的菜\n• 任何健康饮食问题\n\n有什么想问的吗？",
      },
    ]);
    setShowHistory(false);
  };

  const handleSend = async (text?: string) => {
    const content = text || input.trim();
    if (!content || sending) return;

    const userMsg: Message = { role: "user", content };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setSending(true);

    try {
      const { data } = await api.post("/chat/send", {
        content,
        session_id: sessionId,
      });

      const aiMsg: Message = {
        id: data.id,
        role: "assistant",
        content: data.content,
        session_id: data.session_id,
        actions: data.actions || [],
      };
      setMessages((prev) => [...prev, aiMsg]);
      if (data.session_id) {
        setSessionId(data.session_id);
      }

      // 处理 AI 返回的 Action
      if (data.actions) {
        for (const action of data.actions) {
          if (action.type === "DIET_RECORD") {
            // 后台调用记录饮食 API
            api.post("/diet/records", {
              food_text: action.data,
              record_date: new Date().toISOString().split('T')[0],
              meal_type: "auto",
            }).catch(() => {});
          }
        }
      }
    } catch (err) {
      toast("error", "连接 AI 服务失败，请稍后重试");
      const aiMsg: Message = {
        role: "assistant",
        content: "抱歉，连接出了点问题，请稍后重试 🙏",
      };
      setMessages((prev) => [...prev, aiMsg]);
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)]">
      {/* Header */}
      <header className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-xl font-bold text-[var(--text-primary)]">💬 AI 健康助手</h1>
          <p className="text-sm text-[var(--text-muted)]">基于你的饮食数据个性化回答</p>
        </div>
      </header>

      {/* 对话历史按钮 + 新建对话 */}
      <div className="flex items-center justify-between mb-4">
        <button
          onClick={() => setShowHistory(!showHistory)}
          className="px-3 py-1.5 text-sm text-[var(--text-secondary)] border border-[var(--border-default)] rounded-lg hover:bg-[var(--bg-subtle)] transition-colors"
        >
          📜 对话历史
        </button>
        <button
          onClick={handleNewChat}
          className="px-3 py-1.5 text-sm text-[var(--primary)] border border-[var(--primary)] rounded-lg hover:bg-[var(--bg-subtle)] transition-colors"
        >
          + 新建对话
        </button>
      </div>

      {/* 历史面板（展开时显示） */}
      {showHistory && (
        <div className="mb-4 border border-[var(--border-default)] rounded-lg overflow-hidden max-h-60 overflow-y-auto">
          {loadingSessions ? (
            <div className="px-4 py-3 text-sm text-[var(--text-muted)]">加载中...</div>
          ) : sessions.length === 0 ? (
            <div className="px-4 py-3 text-sm text-[var(--text-muted)]">暂无历史对话</div>
          ) : (
            sessions.map((s) => (
              <button
                key={s.session_id}
                onClick={() => loadSession(s.session_id)}
                className="w-full px-4 py-3 text-left hover:bg-[var(--bg-subtle)] border-b border-[var(--border-default)] last:border-0 transition-colors"
              >
                <div className="text-sm font-medium truncate text-[var(--text-primary)]">
                  会话 {new Date(s.last_message_at).toLocaleDateString()}
                </div>
                <div className="text-xs text-[var(--text-muted)]">
                  {s.message_count} 条消息
                </div>
              </button>
            ))
          )}
        </div>
      )}

      {/* Quick Questions */}
      {messages.length <= 1 && (
        <div className="flex flex-wrap gap-2 mb-4">
          {quickQuestions.map((q) => (
            <button
              key={q}
              onClick={() => handleSend(q)}
              className="px-3 py-1.5 bg-green-50 text-green-700 text-xs rounded-full hover:bg-green-100 transition-colors"
            >
              {q}
            </button>
          ))}
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-auto py-4 space-y-4">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex gap-2 ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            {msg.role === "assistant" && (
              <div className="w-7 h-7 bg-green-100 rounded-full flex items-center justify-center shrink-0">
                <Bot className="w-4 h-4 text-green-600" />
              </div>
            )}
            <div
              className={`max-w-[80%] px-3 py-2 rounded-xl text-sm whitespace-pre-wrap ${
                msg.role === "user"
                  ? "bg-green-500 text-white rounded-br-sm"
                  : "bg-gray-100 text-gray-800 rounded-bl-sm"
              }`}
            >
              {msg.content}
              {msg.actions && msg.actions.length > 0 && (
                <div className="mt-2 space-y-1">
                  {msg.actions.map((action, idx) => (
                    <div key={idx} className="flex items-center gap-2 px-2 py-1.5 rounded-lg text-xs"
                      style={{ background: "var(--bg-subtle)", color: "var(--text-secondary)" }}>
                      {action.type === "DIET_RECORD" && (
                        <>
                          <span>📝 已记录饮食</span>
                          <span className="truncate max-w-[200px]">{action.data}</span>
                        </>
                      )}
                      {action.type === "MEAL_LINK" && (
                        <>
                          <span>🍽️ 已关联餐食计划</span>
                          <span className="truncate max-w-[200px]">{action.data}</span>
                        </>
                      )}
                      {action.type === "PROFILE_UPDATE" && (
                        <>
                          <span>👤 已更新画像</span>
                          <span className="truncate max-w-[200px]">{action.data}</span>
                        </>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
            {msg.role === "user" && (
              <div className="w-7 h-7 bg-gray-200 rounded-full flex items-center justify-center shrink-0">
                <User className="w-4 h-4 text-gray-600" />
              </div>
            )}
          </div>
        ))}

        {/* AI 解析中的 Loading 状态 - 脉冲动画 */}
        {sending && (
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-full bg-[var(--ai)] flex items-center justify-center text-white text-sm">
              🤖
            </div>
            <div className="bg-[var(--bg-card)] border border-[var(--border-default)] rounded-2xl rounded-tl-sm px-4 py-3 max-w-[80%]">
              <div className="flex items-center gap-2 mb-2">
                <span className="inline-block w-2 h-2 rounded-full bg-[var(--ai)] animate-pulse" />
                <span className="inline-block w-2 h-2 rounded-full bg-[var(--ai)] animate-pulse [animation-delay:0.2s]" />
                <span className="inline-block w-2 h-2 rounded-full bg-[var(--ai)] animate-pulse [animation-delay:0.4s]" />
                <span className="text-sm text-[var(--text-secondary)] ml-1">AI 正在思考...</span>
              </div>
              <div className="text-xs text-[var(--text-muted)]">
                分析饮食 · 生成建议
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Input */}
      <div className="border-t border-gray-100 pt-3">
        <div className="flex gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
            placeholder="输入你的问题..."
            className="flex-1 px-4 py-2.5 bg-gray-50 rounded-full text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
          />
          <button
            onClick={() => handleSend()}
            disabled={sending || !input.trim()}
            className="w-10 h-10 bg-green-500 rounded-full flex items-center justify-center hover:bg-green-600 transition-colors disabled:opacity-50"
          >
            <Send className="w-4 h-4 text-white" />
          </button>
        </div>
      </div>
    </div>
  );
}