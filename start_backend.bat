@echo off
REM ===== 修改下面三行，填入你自己的 AI 服务信息 =====
set CHATBOT_API_URL=https://api.openai.com/v1/chat/completions
set CHATBOT_API_KEY=你的sk-开头密钥
set CHATBOT_MODEL=gpt-4o-mini
REM ===================================================

cd /d "%~dp0"
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
pause
