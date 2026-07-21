import React, { useState, useRef, useEffect } from 'react';
import {
  X, Send, Bot, User, ChevronDown, ChevronRight,
  Database, Radio, BarChart3, CheckCircle2,
} from 'lucide-react';
import ChatChart from './ChatChart';
import './ChatPanel.css';

const API_BASE = 'http://127.0.0.1:8004';

/* -----------------------------------------------------------------------
   Simple markdown renderer (bold, lists, code, paragraphs)
   ----------------------------------------------------------------------- */
function renderMarkdown(text) {
  if (!text) return null;

  const lines = text.split('\n');
  const elements = [];
  let currentList = null;
  let listType = null;

  const processInline = (line) => {
    // Bold: **text**
    const parts = [];
    let remaining = line;
    let key = 0;

    while (remaining) {
      const boldMatch = remaining.match(/\*\*(.+?)\*\*/);
      const codeMatch = remaining.match(/`([^`]+)`/);

      let firstMatch = null;
      let matchType = null;

      if (boldMatch && (!codeMatch || boldMatch.index <= codeMatch.index)) {
        firstMatch = boldMatch;
        matchType = 'bold';
      } else if (codeMatch) {
        firstMatch = codeMatch;
        matchType = 'code';
      }

      if (!firstMatch) {
        if (remaining) parts.push(remaining);
        break;
      }

      if (firstMatch.index > 0) {
        parts.push(remaining.slice(0, firstMatch.index));
      }

      if (matchType === 'bold') {
        parts.push(<strong key={key++}>{firstMatch[1]}</strong>);
      } else {
        parts.push(<code key={key++}>{firstMatch[1]}</code>);
      }

      remaining = remaining.slice(firstMatch.index + firstMatch[0].length);
    }

    return parts;
  };

  const flushList = () => {
    if (currentList && currentList.length > 0) {
      const Tag = listType === 'ol' ? 'ol' : 'ul';
      elements.push(
        <Tag key={`list-${elements.length}`}>
          {currentList.map((item, i) => (
            <li key={i}>{processInline(item)}</li>
          ))}
        </Tag>
      );
      currentList = null;
      listType = null;
    }
  };

  lines.forEach((line, i) => {
    const trimmed = line.trim();

    // Unordered list
    const ulMatch = trimmed.match(/^[-*]\s+(.+)/);
    if (ulMatch) {
      if (listType !== 'ul') flushList();
      if (!currentList) { currentList = []; listType = 'ul'; }
      currentList.push(ulMatch[1]);
      return;
    }

    // Ordered list
    const olMatch = trimmed.match(/^\d+[.)]\s+(.+)/);
    if (olMatch) {
      if (listType !== 'ol') flushList();
      if (!currentList) { currentList = []; listType = 'ol'; }
      currentList.push(olMatch[1]);
      return;
    }

    flushList();

    // Empty line
    if (!trimmed) return;

    // Heading-like (## Sources etc.)
    const headingMatch = trimmed.match(/^#{1,3}\s+(.+)/);
    if (headingMatch) {
      elements.push(
        <p key={i} style={{ fontWeight: 600, marginTop: '0.6em' }}>
          {processInline(headingMatch[1])}
        </p>
      );
      return;
    }

    // Normal paragraph
    elements.push(<p key={i}>{processInline(trimmed)}</p>);
  });

  flushList();
  return elements;
}

/* -----------------------------------------------------------------------
   Citations (collapsible)
   ----------------------------------------------------------------------- */
function Citations({ citations }) {
  const [open, setOpen] = useState(false);

  if (!citations || citations.length === 0) return null;

  const iconForTool = (tool) => {
    if (tool.startsWith('query_dnac') || tool === 'query_dnac_issue' || tool === 'query_dnac_device_health') {
      return <Radio size={11} />;
    }
    if (tool === 'generate_visualization') return <BarChart3 size={11} />;
    return <Database size={11} />;
  };

  return (
    <div className="chat-citations">
      <button className="chat-citations-toggle" onClick={() => setOpen(!open)}>
        {open ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
        {citations.length} source{citations.length !== 1 ? 's' : ''} cited
      </button>
      {open && (
        <div className="chat-citations-list">
          {citations.map((c, i) => (
            <div key={i} className="chat-citation-item">
              {iconForTool(c.tool)}
              <span className="citation-tool">{c.tool}</span>
              <span>{c.summary}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

/* -----------------------------------------------------------------------
   Task indicators (Copilot-style)
   ----------------------------------------------------------------------- */
function TaskIndicators({ tasks, isLoading }) {
  if (!tasks || tasks.length === 0) return null;

  return (
    <div className="chat-tasks">
      {tasks.map((label, i) => {
        const isLast = i === tasks.length - 1;
        const isActive = isLast && isLoading;
        return (
          <div key={i} className={`chat-task-pill ${isActive ? 'active' : 'done'}`}>
            {isActive ? (
              <div className="chat-task-spinner" />
            ) : (
              <CheckCircle2 size={12} />
            )}
            {label}
          </div>
        );
      })}
    </div>
  );
}

/* -----------------------------------------------------------------------
   Main ChatPanel component
   ----------------------------------------------------------------------- */
function ChatPanel({ isOpen, onClose }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [activeTasks, setActiveTasks] = useState([]);
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, activeTasks]);

  // Focus input when panel opens
  useEffect(() => {
    if (isOpen) {
      setTimeout(() => textareaRef.current?.focus(), 350);
    }
  }, [isOpen]);

  const sendMessage = async (text) => {
    const userMessage = text || input.trim();
    if (!userMessage || isLoading) return;

    setInput('');
    setIsLoading(true);
    setActiveTasks([]);

    // Add user message
    const newMessages = [...messages, { role: 'user', text: userMessage }];
    setMessages(newMessages);

    // Build history for context (exclude charts/citations metadata)
    const history = newMessages.map((m) => ({ role: m.role, text: m.text }));

    try {
      const response = await fetch(`${API_BASE}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMessage, history: history.slice(0, -1) }),
      });

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        // Process SSE lines
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          try {
            const event = JSON.parse(line.slice(6));
            handleSSEvent(event, newMessages);
          } catch {
            // skip malformed lines
          }
        }
      }

      // Process remaining buffer
      if (buffer.startsWith('data: ')) {
        try {
          const event = JSON.parse(buffer.slice(6));
          handleSSEvent(event, newMessages);
        } catch {
          // skip
        }
      }
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          text: `Sorry, I couldn't connect to the API. Please check if the dashboard API is running.\n\nError: ${err.message}`,
          citations: [],
          charts: [],
        },
      ]);
    } finally {
      setIsLoading(false);
      setActiveTasks([]);
    }
  };

  const handleSSEvent = (event, baseMessages) => {
    switch (event.type) {
      case 'task':
        setActiveTasks((prev) => [...prev, event.label]);
        break;

      case 'clarification':
        setMessages((prev) => [
          ...prev,
          {
            role: 'assistant',
            text: event.text,
            suggestions: event.suggestions || [],
            citations: [],
            charts: [],
          },
        ]);
        break;

      case 'answer':
        setMessages((prev) => [
          ...prev,
          {
            role: 'assistant',
            text: event.text || '',
            citations: event.citations || [],
            charts: event.charts || [],
          },
        ]);
        break;

      case 'error':
        setMessages((prev) => [
          ...prev,
          {
            role: 'assistant',
            text: `Error: ${event.text}`,
            citations: [],
            charts: [],
          },
        ]);
        break;

      case 'done':
        setIsLoading(false);
        break;

      default:
        break;
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const handleSuggestionClick = (suggestion) => {
    sendMessage(suggestion);
  };

  // Auto-resize textarea
  const handleInputChange = (e) => {
    setInput(e.target.value);
    const ta = e.target;
    ta.style.height = 'auto';
    ta.style.height = Math.min(ta.scrollHeight, 120) + 'px';
  };

  if (!isOpen) return null;

  return (
    <>
      <div className="chat-overlay" onClick={onClose} />
      <div className="chat-panel">
        {/* Header */}
        <div className="chat-header">
          <div className="chat-header-icon">
            <Bot size={18} color="#fff" />
          </div>
          <div className="chat-header-text">
            <h3>DNAC Ops Assistant</h3>
            <span>AI-powered network insights</span>
          </div>
          <button className="chat-close-btn" onClick={onClose}>
            <X size={18} />
          </button>
        </div>

        {/* Messages */}
        <div className="chat-messages">
          {messages.length === 0 && (
            <div className="chat-msg chat-msg-assistant" style={{ opacity: 0.7 }}>
              <div className="chat-msg-bubble">
                <p>
                  Hi! I'm your <strong>DNAC Ops Assistant</strong>.
                  I can help you with:
                </p>
                <ul>
                  <li>Alert status and history for specific devices</li>
                  <li>Suppression rate and KPI metrics</li>
                  <li>Live device status from DNAC</li>
                  <li>Charts and visualizations of alert data</li>
                </ul>
                <p>Ask me anything about your network operations!</p>
              </div>
            </div>
          )}

          {messages.map((msg, i) => (
            <div key={i} className={`chat-msg chat-msg-${msg.role}`}>
              <div className="chat-msg-role">
                {msg.role === 'user' ? (
                  <><User size={10} /> You</>
                ) : (
                  <><Bot size={10} /> Assistant</>
                )}
              </div>
              <div className="chat-msg-bubble">
                {msg.role === 'assistant' ? renderMarkdown(msg.text) : msg.text}
              </div>

              {/* Charts */}
              {msg.charts && msg.charts.length > 0 && (
                msg.charts.map((chart, ci) => (
                  <ChatChart key={ci} spec={chart} />
                ))
              )}

              {/* Suggestion chips */}
              {msg.suggestions && msg.suggestions.length > 0 && (
                <div className="chat-suggestions">
                  {msg.suggestions.map((s, si) => (
                    <button
                      key={si}
                      className="chat-suggestion-chip"
                      onClick={() => handleSuggestionClick(s)}
                    >
                      {s}
                    </button>
                  ))}
                </div>
              )}

              {/* Citations */}
              {msg.citations && msg.citations.length > 0 && (
                <Citations citations={msg.citations} />
              )}
            </div>
          ))}

          {/* Active task indicators */}
          {isLoading && activeTasks.length > 0 && (
            <div className="chat-msg chat-msg-assistant">
              <div className="chat-msg-role">
                <Bot size={10} /> Assistant
              </div>
              <TaskIndicators tasks={activeTasks} isLoading={isLoading} />
            </div>
          )}

          {/* Loading with no tasks yet */}
          {isLoading && activeTasks.length === 0 && (
            <div className="chat-msg chat-msg-assistant">
              <div className="chat-msg-role">
                <Bot size={10} /> Assistant
              </div>
              <div className="chat-task-pill active">
                <div className="chat-task-spinner" />
                Thinking...
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="chat-input-area">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            placeholder="Ask about alerts, devices, or metrics..."
            rows={1}
            disabled={isLoading}
          />
          <button
            className="chat-send-btn"
            onClick={() => sendMessage()}
            disabled={isLoading || !input.trim()}
          >
            <Send size={16} />
          </button>
        </div>
      </div>
    </>
  );
}

export default ChatPanel;
