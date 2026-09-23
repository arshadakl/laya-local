# Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────┐
│                    laya-local                           │
│                                                         │
│  ┌──────────┐   ┌──────────────┐   ┌────────────────┐  │
│  │ Listener │──▶│ Transcriber  │──▶│  Classifier    │  │
│  │ (Mic +   │   │ (faster-     │   │  (Laya         │  │
│  │  VAD)    │   │  whisper)    │   │  multilingual) │  │
│  └──────────┘   └──────────────┘   └───────┬────────┘  │
│                                            │           │
│                                            ▼           │
│  ┌──────────┐   ┌──────────────┐   ┌────────────────┐  │
│  │Responder │◀──│   Executor   │◀──│  Intent        │  │
│  │ (Piper   │   │  (Whitelist  │   │  (action +     │  │
│  │  TTS)    │   │   dispatch)  │   │   target)      │  │
│  └──────────┘   └──────────────┘   └────────────────┘  │
│                       │                                 │
│                       ▼                                 │
│              ┌────────────────┐                         │
│              │    Actions     │                         │
│              │  ┌──────────┐  │                         │
│              │  │ Apps     │  │                         │
│              │  │ Files    │  │                         │
│              │  │ Browser  │  │                         │
│              │  │ System   │  │                         │
│              │  │ Media    │  │                         │
│              │  │ Custom   │  │                         │
│              │  └──────────┘  │                         │
│              └────────────────┘                         │
└─────────────────────────────────────────────────────────┘
```

## Data Flow

1. **Input**: User speaks (push-to-talk) or types a command
2. **STT**: faster-whisper converts audio to text (local, no cloud)
3. **Classification**: Laya multilingual classifies intent in ~35ms
4. **Dispatch**: Executor routes to whitelisted action handler
5. **Action**: Handler executes the Windows command
6. **Response**: Optional TTS feedback or console output

## Components

### Listener (`core/listener.py`)
- Captures microphone audio via `sounddevice`
- Push-to-talk with configurable trigger key
- Voice Activity Detection (VAD) for auto-stop
- Max duration limit to prevent runaway recording

### Transcriber (`core/transcriber.py`)
- Wraps faster-whisper for local speech-to-text
- Lazy model loading (only loads on first use)
- Supports Malayalam, English, and mixed languages
- Returns transcribed text with language detection

### Classifier (`core/classifier.py`)
- Wraps Laya Router for intent classification
- Evaluates 5 question categories in a single forward pass
- Confidence gating (rejects below 40% threshold)
- Returns structured intent with action + target

### Executor (`core/executor.py`)
- Whitelist-based action dispatch
- Only pre-registered actions can execute
- Error handling and logging for all actions
- Supports custom user-defined actions

### Actions (`actions/`)
- **apps.py**: Open/close 20+ whitelisted applications
- **files.py**: Open known folders and file paths
- **browser.py**: Open URLs and web search
- **system.py**: Shutdown, restart, lock, volume, mute
- **media.py**: Play/pause, next/prev, volume control
- **custom.py**: User-defined actions from config.yaml

### Responder (`responder/tts.py`)
- Piper TTS for spoken feedback
- Graceful fallback when TTS unavailable
- Only active when enabled in config

## Security Model

- **Whitelist only**: Only pre-registered actions can execute
- **No shell injection**: Actions use explicit command maps
- **No arbitrary execution**: `os.system()` and `subprocess` with user input are forbidden
- **Config validation**: Custom actions require explicit command or path

## Configuration

All settings are in `config.yaml` (see `config.example.yaml`):
- Whisper model size and device
- Laya model and device
- TTS enable/disable and voice
- Listener trigger key and thresholds
- Custom action definitions
