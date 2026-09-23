# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-09-23

### Added

- Initial project scaffolding with src layout
- Laya multilingual integration for Malayalam/English intent classification
- faster-whisper integration for local speech-to-text
- Piper TTS integration for voice responses
- Push-to-talk listener with VAD
- Whitelist-based action executor for safe command execution
- Application launcher (Chrome, VS Code, Terminal, Discord, Spotify)
- Folder/file opener (Downloads, Documents, Desktop)
- System controls (shutdown, restart, lock, volume)
- Media playback controls
- Custom user-defined actions via YAML config
- Structured logging with structlog
- GitHub Actions CI pipeline
- Pre-commit hooks with ruff, mypy, and conventional commits
