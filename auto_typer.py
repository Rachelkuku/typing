#!/usr/bin/env python3
"""
Auto Typer - 웹 브라우저 기반
"""

import threading
import time
import json
import webbrowser
import pyperclip
from http.server import HTTPServer, BaseHTTPRequestHandler
from pynput.keyboard import Controller as KeyboardController

keyboard = KeyboardController()
stop_flag = threading.Event()
pause_event = threading.Event()
pause_event.set()

status = {"state": "idle", "message": "대기 중", "progress": 0, "total": 0}

HTML = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Auto Typer ⌨️</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: #0f0d1a;
    color: #ede9fe;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    display: flex;
    justify-content: center;
    padding: 32px 16px;
    min-height: 100vh;
  }
  .container { width: 100%; max-width: 500px; }
  h1 { font-size: 28px; color: #c4b5fd; margin-bottom: 4px; }
  .subtitle { font-size: 13px; color: #6b7280; margin-bottom: 20px; }
  .card {
    background: #1e1b2e;
    border: 1px solid #3d3460;
    border-radius: 16px;
    padding: 20px;
    margin-bottom: 12px;
  }
  .card-label {
    font-size: 13px;
    font-weight: 600;
    color: #a78bfa;
    margin-bottom: 10px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  .card-label span { font-weight: 400; color: #c4b5fd; font-size: 12px; }
  textarea {
    width: 100%;
    height: 180px;
    background: #0f0d1a;
    color: #ede9fe;
    border: 1px solid #6d28d9;
    border-radius: 10px;
    padding: 12px;
    font-size: 13px;
    resize: vertical;
    outline: none;
    font-family: inherit;
    line-height: 1.6;
  }
  textarea:focus { border-color: #8b5cf6; }
  .btn-row { display: flex; gap: 8px; margin-top: 10px; }
  button {
    cursor: pointer;
    border: none;
    border-radius: 8px;
    font-size: 13px;
    font-weight: 600;
    padding: 9px 16px;
    transition: background 0.15s;
  }
  .btn-purple { background: #8b5cf6; color: #0f0d1a; }
  .btn-purple:hover { background: #a78bfa; }
  .btn-gray { background: #252238; color: #ede9fe; }
  .btn-gray:hover { background: #3d3460; }
  .slider-row { display: flex; flex-direction: column; gap: 4px; }
  input[type=range] {
    width: 100%;
    accent-color: #8b5cf6;
    cursor: pointer;
  }
  .slider-hints { display: flex; justify-content: space-between; font-size: 10px; color: #6b7280; }
  .divider { border: none; border-top: 1px solid #3d3460; margin: 14px 0; }
  #status {
    text-align: center;
    font-size: 14px;
    font-weight: 600;
    padding: 8px 0 4px;
    color: #6b7280;
  }
  .progress-bar-wrap {
    background: #252238;
    border-radius: 999px;
    height: 6px;
    margin: 4px 0 12px;
    overflow: hidden;
  }
  #progress-bar {
    height: 100%;
    background: #8b5cf6;
    border-radius: 999px;
    width: 0%;
    transition: width 0.3s;
  }
  .ctrl-row { display: flex; gap: 8px; }
  .ctrl-row button { flex: 1; padding: 14px; font-size: 14px; border-radius: 12px; }
  #btn-start { background: #8b5cf6; color: #0f0d1a; }
  #btn-start:hover:not(:disabled) { background: #a78bfa; }
  #btn-pause { background: #252238; color: #ede9fe; }
  #btn-pause:hover:not(:disabled) { background: #3d3460; }
  #btn-stop  { background: #3b1a3a; color: #ede9fe; }
  #btn-stop:hover:not(:disabled)  { background: #5b2d59; }
  button:disabled { opacity: 0.4; cursor: not-allowed; }
</style>
</head>
<body>
<div class="container">
  <h1>⌨️ Auto Typer</h1>
  <p class="subtitle">텍스트를 붙여넣고 원하는 창에 자동으로 타이핑하세요</p>

  <div class="card">
    <div class="card-label">타이핑할 텍스트 <span id="char-count">0 글자</span></div>
    <textarea id="text-input" placeholder="여기에 텍스트를 입력하거나 클립보드에서 붙여넣으세요…"></textarea>
    <div class="btn-row">
      <button class="btn-purple" onclick="pasteClipboard()">📋 클립보드 붙여넣기</button>
      <button class="btn-gray"   onclick="clearText()">🗑 지우기</button>
    </div>
  </div>

  <div class="card">
    <div class="card-label">⚡ 타이핑 속도 <span id="speed-label">50ms / 글자</span></div>
    <div class="slider-row">
      <input type="range" id="speed" min="5" max="500" value="50"
             oninput="document.getElementById('speed-label').textContent = this.value + 'ms / 글자'">
      <div class="slider-hints"><span>빠름 (5ms)</span><span>느림 (500ms)</span></div>
    </div>
    <hr class="divider">
    <div class="card-label">⏱ 시작 딜레이 <span id="delay-label">3초</span></div>
    <div class="slider-row">
      <input type="range" id="delay" min="1" max="15" value="3"
             oninput="document.getElementById('delay-label').textContent = this.value + '초'">
    </div>
  </div>

  <div id="status">대기 중</div>
  <div class="progress-bar-wrap"><div id="progress-bar"></div></div>

  <div class="ctrl-row">
    <button id="btn-start" onclick="startTyping()">▶ 시작</button>
    <button id="btn-pause" onclick="togglePause()" disabled>⏸ 일시정지</button>
    <button id="btn-stop"  onclick="stopTyping()"  disabled>⏹ 중단</button>
  </div>
</div>

<script>
const textInput = document.getElementById('text-input');
textInput.addEventListener('input', () => {
  document.getElementById('char-count').textContent = textInput.value.length.toLocaleString() + ' 글자';
});

async function pasteClipboard() {
  const res = await fetch('/api/clipboard');
  const data = await res.json();
  textInput.value = data.text;
  textInput.dispatchEvent(new Event('input'));
}

function clearText() {
  textInput.value = '';
  textInput.dispatchEvent(new Event('input'));
}

async function startTyping() {
  const text = textInput.value;
  if (!text.trim()) { setStatus('⚠️ 텍스트를 먼저 입력해주세요', 'error'); return; }
  await fetch('/api/start', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      text,
      speed: parseInt(document.getElementById('speed').value),
      delay: parseInt(document.getElementById('delay').value)
    })
  });
  setButtons(true);
  poll();
}

async function togglePause() {
  await fetch('/api/pause', { method: 'POST' });
}

async function stopTyping() {
  await fetch('/api/stop', { method: 'POST' });
}

function setButtons(running) {
  document.getElementById('btn-start').disabled = running;
  document.getElementById('btn-pause').disabled = !running;
  document.getElementById('btn-stop').disabled  = !running;
}

const colors = {
  idle: '#6b7280', countdown: '#fbbf24', typing: '#34d399',
  paused: '#fbbf24', done: '#34d399', stopped: '#f87171', error: '#f87171'
};

function setStatus(msg, state) {
  const el = document.getElementById('status');
  el.textContent = msg;
  el.style.color = colors[state] || '#6b7280';
}

let pollTimer = null;
function poll() {
  clearTimeout(pollTimer);
  pollTimer = setTimeout(async () => {
    try {
      const res = await fetch('/api/status');
      const s = await res.json();
      setStatus(s.message, s.state);
      const pct = s.total > 0 ? (s.progress / s.total * 100) : 0;
      document.getElementById('progress-bar').style.width = pct + '%';
      if (s.state === 'pause_pending') {
        document.getElementById('btn-pause').textContent = '▶ 계속';
      } else {
        document.getElementById('btn-pause').textContent = '⏸ 일시정지';
      }
      if (s.state === 'idle' || s.state === 'done' || s.state === 'stopped' || s.state === 'error') {
        setButtons(false);
        if (s.state === 'done' || s.state === 'stopped') {
          document.getElementById('progress-bar').style.width = s.state === 'done' ? '100%' : '0%';
        }
      } else {
        poll();
      }
    } catch(e) { poll(); }
  }, 300);
}
</script>
</body>
</html>"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def _send(self, code, content_type, body):
        if isinstance(body, str):
            body = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/":
            self._send(200, "text/html; charset=utf-8", HTML)
        elif self.path == "/api/clipboard":
            try:
                text = pyperclip.paste()
            except Exception:
                text = ""
            self._send(200, "application/json", json.dumps({"text": text}))
        elif self.path == "/api/status":
            self._send(200, "application/json", json.dumps(status))
        else:
            self._send(404, "text/plain", "Not found")

    def do_POST(self):
        if self.path == "/api/start":
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length))
            threading.Thread(target=run_typing, args=(body,), daemon=True).start()
            self._send(200, "application/json", '{"ok":true}')
        elif self.path == "/api/pause":
            if pause_event.is_set():
                pause_event.clear()
                status["state"] = "pause_pending"
                status["message"] = "⏸ 일시정지됨"
            else:
                pause_event.set()
                status["state"] = "typing"
                status["message"] = "⌨️ 타이핑 중…"
            self._send(200, "application/json", '{"ok":true}')
        elif self.path == "/api/stop":
            stop_flag.set()
            pause_event.set()
            status["state"] = "stopped"
            status["message"] = "⏹ 중단됨"
            self._send(200, "application/json", '{"ok":true}')
        else:
            self._send(404, "text/plain", "Not found")


def run_typing(body):
    global status
    text  = body["text"]
    speed = body["speed"] / 1000.0
    delay = body["delay"]

    stop_flag.clear()
    pause_event.set()
    status = {"state": "countdown", "message": "", "progress": 0, "total": len(text)}

    for i in range(delay, 0, -1):
        if stop_flag.is_set():
            return
        status["message"] = f"⏳ {i}초 후 시작 — 타이핑할 창으로 이동하세요…"
        time.sleep(1)

    if stop_flag.is_set():
        return

    status["state"] = "typing"
    status["message"] = "⌨️ 타이핑 중…"

    for idx, char in enumerate(text):
        if stop_flag.is_set():
            break
        pause_event.wait()
        if stop_flag.is_set():
            break
        try:
            keyboard.type(char)
        except Exception:
            pass
        time.sleep(speed)
        if idx % 10 == 0:
            pct = int((idx + 1) / len(text) * 100)
            status["progress"] = idx + 1
            status["message"] = f"⌨️ 타이핑 중… {pct}% ({idx+1}/{len(text)})"

    if not stop_flag.is_set():
        status["state"] = "done"
        status["message"] = "✅ 타이핑 완료!"
        status["progress"] = len(text)
    else:
        status["state"] = "stopped"
        status["message"] = "⏹ 중단됨"


if __name__ == "__main__":
    port = 8765
    server = HTTPServer(("127.0.0.1", port), Handler)
    print(f"Auto Typer 실행 중 → http://localhost:{port}")
    print("종료하려면 Ctrl+C")
    webbrowser.open(f"http://localhost:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n종료됨")
