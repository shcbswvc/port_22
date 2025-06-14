# Team port_22
> Dhruv Mahajan, CM Shaik Abdul Rahim Batcha, Monisha P

## Scroll Breaker

A focus app that helps break scrolling habits using AI-powered notifications.

## Features

- Smart notification generation using LLMs (Gemini or Local Llama via Ollama)
- Context-aware task selection
- Progress tracking and performance analysis
- Fallback templates when LLM is unavailable
- Adaptive feedback system

## Setup

1. Clone the repository:
```bash
git clone https://github.com/shcbswvc/port_22.git
cd port_22
```

2. Install dependencies:
```bash
pip install -e .
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. For local LLM support:
- Install Ollama from [ollama.ai](https://ollama.ai)
- Pull the Llama model: `ollama pull llama3.2:3b`

## Configuration

The app can be configured to use different LLM providers:
- Gemini (Cloud-based)
- Local (Ollama with Llama3.2)
- None (Uses template-based notifications)

## Usage

Run the demo:
```bash
python -m src.demo
```

## Architecture

- `src/core/`: Core application logic
- `src/notifications/`: Notification generation and templates
- `src/database/`: Data persistence
- `src/models/`: Data models

## License

MIT
