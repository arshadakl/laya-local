"""Voice assistant GUI built with tkinter.

Provides a dark-themed, modern interface with animated mic indicator,
real-time transcription display, and action result feedback.
"""

from __future__ import annotations

import math
import threading
import tkinter as tk
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from laya_local.core.classifier import Classifier
    from laya_local.core.executor import Executor
    from laya_local.core.listener import Listener
    from laya_local.core.transcriber import Transcriber

# ── Color palette (dark theme) ────────────────────────────────────
_BG = "#0d1117"
_BG_SECONDARY = "#161b22"
_BG_TERTIARY = "#21262d"
_TEXT = "#e6edf3"
_TEXT_DIM = "#8b949e"
_ACCENT = "#58a6ff"
_ACCENT_GREEN = "#3fb950"
_ACCENT_RED = "#f85149"
_ACCENT_YELLOW = "#d29922"
_ACCENT_PURPLE = "#bc8cff"

# ── States ────────────────────────────────────────────────────────
STATE_IDLE = "idle"
STATE_LISTENING = "listening"
STATE_PROCESSING = "processing"
STATE_RESULT = "result"
STATE_ERROR = "error"


class AssistantUI:
    """Main voice assistant GUI window.

    Displays a dark-themed interface with:
    - Animated microphone indicator (pulsing circle)
    - Current state label (Idle / Listening / Processing)
    - Transcribed text display
    - Action result display
    - Status bar with shortcuts

    Args:
        listener: Audio listener component.
        transcriber: Speech-to-text component.
        classifier: Intent classification component.
        executor: Action execution component.
    """

    def __init__(
        self,
        listener: Listener,
        transcriber: Transcriber,
        classifier: Classifier,
        executor: Executor,
    ) -> None:
        self._listener = listener
        self._transcriber = transcriber
        self._classifier = classifier
        self._executor = executor

        self._state = STATE_IDLE
        self._pulse_angle = 0.0
        self._is_listening = False
        self._should_stop = False

        # Build the window
        self._root = tk.Tk()
        self._root.title("laya-local")
        self._root.geometry("520x600")
        self._root.configure(bg=_BG)
        self._root.resizable(False, False)

        # Handle window close
        self._root.protocol("WM_DELETE_WINDOW", self._on_close)

        # Build UI elements
        self._build_ui()

        # Start animation loop
        self._animate()

    def _build_ui(self) -> None:
        """Build all UI elements."""
        # ── Title bar ─────────────────────────────────────────────
        title_frame = tk.Frame(self._root, bg=_BG, height=50)
        title_frame.pack(fill=tk.X, padx=20, pady=(20, 0))

        tk.Label(
            title_frame,
            text="laya-local",
            font=("Segoe UI", 16, "bold"),
            fg=_ACCENT,
            bg=_BG,
        ).pack(side=tk.LEFT)

        tk.Label(
            title_frame,
            text="v0.1.0",
            font=("Segoe UI", 10),
            fg=_TEXT_DIM,
            bg=_BG,
        ).pack(side=tk.LEFT, padx=(8, 0), pady=(4, 0))

        # ── Mic indicator area ────────────────────────────────────
        self._mic_canvas = tk.Canvas(
            self._root,
            width=200,
            height=200,
            bg=_BG,
            highlightthickness=0,
        )
        self._mic_canvas.pack(pady=(30, 10))

        # ── State label ───────────────────────────────────────────
        self._state_label = tk.Label(
            self._root,
            text="Press Ctrl to speak",
            font=("Segoe UI", 13),
            fg=_TEXT_DIM,
            bg=_BG,
        )
        self._state_label.pack(pady=(0, 20))

        # ── Transcript card ───────────────────────────────────────
        transcript_card = tk.Frame(self._root, bg=_BG_SECONDARY, bd=0)
        transcript_card.pack(fill=tk.X, padx=20, pady=(0, 10))

        tk.Label(
            transcript_card,
            text="  HEARD",
            font=("Segoe UI", 9, "bold"),
            fg=_TEXT_DIM,
            bg=_BG_SECONDARY,
            anchor="w",
        ).pack(fill=tk.X, padx=10, pady=(8, 0))

        self._transcript_label = tk.Label(
            transcript_card,
            text="...",
            font=("Segoe UI", 12),
            fg=_TEXT,
            bg=_BG_SECONDARY,
            anchor="w",
            wraplength=460,
            justify=tk.LEFT,
        )
        self._transcript_label.pack(fill=tk.X, padx=10, pady=(4, 10))

        # ── Result card ───────────────────────────────────────────
        result_card = tk.Frame(self._root, bg=_BG_SECONDARY, bd=0)
        result_card.pack(fill=tk.X, padx=20, pady=(0, 10))

        tk.Label(
            result_card,
            text="  ACTION",
            font=("Segoe UI", 9, "bold"),
            fg=_TEXT_DIM,
            bg=_BG_SECONDARY,
            anchor="w",
        ).pack(fill=tk.X, padx=10, pady=(8, 0))

        self._result_label = tk.Label(
            result_card,
            text="...",
            font=("Segoe UI", 12),
            fg=_ACCENT_GREEN,
            bg=_BG_SECONDARY,
            anchor="w",
            wraplength=460,
            justify=tk.LEFT,
        )
        self._result_label.pack(fill=tk.X, padx=10, pady=(4, 10))

        # ── History list ──────────────────────────────────────────
        history_frame = tk.Frame(self._root, bg=_BG_SECONDARY, bd=0)
        history_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 10))

        tk.Label(
            history_frame,
            text="  HISTORY",
            font=("Segoe UI", 9, "bold"),
            fg=_TEXT_DIM,
            bg=_BG_SECONDARY,
            anchor="w",
        ).pack(fill=tk.X, padx=10, pady=(8, 0))

        self._history_text = tk.Text(
            history_frame,
            font=("Consolas", 10),
            fg=_TEXT_DIM,
            bg=_BG_SECONDARY,
            bd=0,
            highlightthickness=0,
            state=tk.DISABLED,
            height=6,
        )
        self._history_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=(4, 10))

        # ── Status bar ────────────────────────────────────────────
        status_frame = tk.Frame(self._root, bg=_BG_TERTIARY, height=30)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)

        self._status_label = tk.Label(
            status_frame,
            text="  Hold Ctrl to speak  |  Ctrl+C to quit",
            font=("Segoe UI", 9),
            fg=_TEXT_DIM,
            bg=_BG_TERTIARY,
            anchor="w",
        )
        self._status_label.pack(fill=tk.X, padx=5, pady=2)

    def _draw_mic(self) -> None:
        """Draw the animated microphone indicator."""
        self._mic_canvas.delete("all")

        cx, cy = 100, 100

        if self._state == STATE_IDLE:
            # Static circle
            self._mic_canvas.create_oval(
                cx - 40,
                cy - 40,
                cx + 40,
                cy + 40,
                fill=_BG_TERTIARY,
                outline=_TEXT_DIM,
                width=2,
            )
            # Mic icon (simple)
            self._mic_canvas.create_text(
                cx,
                cy,
                text="🎙",
                font=("Segoe UI Emoji", 24),
            )

        elif self._state == STATE_LISTENING:
            # Pulsing outer rings
            for i in range(3):
                r = 50 + i * 15 + int(8 * math.sin(self._pulse_angle + i * 0.8))
                self._mic_canvas.create_oval(
                    cx - r,
                    cy - r,
                    cx + r,
                    cy + r,
                    outline=_ACCENT,
                    width=2,
                )
            # Center circle
            self._mic_canvas.create_oval(
                cx - 40,
                cy - 40,
                cx + 40,
                cy + 40,
                fill=_ACCENT,
                outline=_ACCENT,
                width=2,
            )
            self._mic_canvas.create_text(
                cx,
                cy,
                text="🎙",
                font=("Segoe UI Emoji", 24),
            )

        elif self._state == STATE_PROCESSING:
            # Spinning dots
            for i in range(8):
                angle = self._pulse_angle + (i * math.pi / 4)
                r = 55
                dx = r * math.cos(angle)
                dy = r * math.sin(angle)
                size = 4 + 2 * math.sin(self._pulse_angle * 2 + i)
                self._mic_canvas.create_oval(
                    cx + dx - size,
                    cy + dy - size,
                    cx + dx + size,
                    cy + dy + size,
                    fill=_ACCENT_PURPLE,
                    outline="",
                )
            self._mic_canvas.create_oval(
                cx - 40,
                cy - 40,
                cx + 40,
                cy + 40,
                fill=_BG_TERTIARY,
                outline=_ACCENT_PURPLE,
                width=2,
            )
            self._mic_canvas.create_text(
                cx,
                cy,
                text="⏳",
                font=("Segoe UI Emoji", 24),
            )

        elif self._state == STATE_RESULT:
            # Green check
            self._mic_canvas.create_oval(
                cx - 40,
                cy - 40,
                cx + 40,
                cy + 40,
                fill=_ACCENT_GREEN,
                outline=_ACCENT_GREEN,
                width=2,
            )
            self._mic_canvas.create_text(
                cx,
                cy,
                text="✓",
                font=("Segoe UI", 30, "bold"),
                fill="white",
            )

        elif self._state == STATE_ERROR:
            # Red X
            self._mic_canvas.create_oval(
                cx - 40,
                cy - 40,
                cx + 40,
                cy + 40,
                fill=_ACCENT_RED,
                outline=_ACCENT_RED,
                width=2,
            )
            self._mic_canvas.create_text(
                cx,
                cy,
                text="✗",
                font=("Segoe UI", 30, "bold"),
                fill="white",
            )

    def _animate(self) -> None:
        """Animation tick — runs every 50ms."""
        if self._should_stop:
            return

        if self._state == STATE_LISTENING or self._state == STATE_PROCESSING:
            self._pulse_angle += 0.15

        self._draw_mic()
        self._root.after(50, self._animate)

    def _set_state(self, state: str) -> None:
        """Update the UI state.

        Args:
            state: One of STATE_IDLE, STATE_LISTENING, etc.
        """
        self._state = state

        labels = {
            STATE_IDLE: ("Press Ctrl to speak", _TEXT_DIM),
            STATE_LISTENING: ("Listening...", _ACCENT),
            STATE_PROCESSING: ("Processing...", _ACCENT_PURPLE),
            STATE_RESULT: ("Done!", _ACCENT_GREEN),
            STATE_ERROR: ("Error", _ACCENT_RED),
        }

        text, color = labels.get(state, ("", _TEXT_DIM))
        self._state_label.config(text=text, fg=color)

    def _update_transcript(self, text: str) -> None:
        """Update the heard text display.

        Args:
            text: Transcribed text to display.
        """
        self._transcript_label.config(text=text)

    def _update_result(self, text: str, color: str = _ACCENT_GREEN) -> None:
        """Update the action result display.

        Args:
            text: Result message to display.
            color: Text color.
        """
        self._result_label.config(text=text, fg=color)

    def _add_history(self, text: str) -> None:
        """Add a line to the history log.

        Args:
            text: Line to append.
        """
        self._history_text.config(state=tk.NORMAL)
        self._history_text.insert(tk.END, text + "\n")
        self._history_text.see(tk.END)
        self._history_text.config(state=tk.DISABLED)

    def _process_command(self, text: str) -> None:
        """Process a voice command in a background thread.

        Args:
            text: Transcribed command text.
        """

        def _worker() -> None:
            try:
                self._root.after(0, self._set_state, STATE_PROCESSING)
                self._root.after(0, self._update_transcript, text)

                # Classify intent
                intent = self._classifier.classify(text)
                if intent is None:
                    msg = f"Could not understand: {text}"
                    self._root.after(0, self._update_result, msg, _ACCENT_YELLOW)
                    self._root.after(0, self._add_history, f"  ⚠ {msg}")
                    self._root.after(0, self._set_state, STATE_ERROR)
                    self._root.after(2000, self._set_state, STATE_IDLE)
                    return

                # Execute action
                result = self._executor.execute(intent)
                action = intent.get("action", "unknown")
                target = intent.get("target", "")
                status = result.get("status", "error")
                message = result.get("message", "")

                if status == "success":
                    display = f"{action} → {target}" if target else action
                    self._root.after(0, self._update_result, display, _ACCENT_GREEN)
                    self._root.after(0, self._add_history, f"  ✓ {text} → {display}")
                else:
                    self._root.after(0, self._update_result, message, _ACCENT_RED)
                    self._root.after(0, self._add_history, f"  ✗ {text} → {message}")

                self._root.after(0, self._set_state, STATE_RESULT)
                self._root.after(2000, self._set_state, STATE_IDLE)

            except Exception as exc:
                msg = f"Error: {exc}"
                self._root.after(0, self._update_result, msg, _ACCENT_RED)
                self._root.after(0, self._add_history, f"  ✗ {msg}")
                self._root.after(0, self._set_state, STATE_ERROR)
                self._root.after(2000, self._set_state, STATE_IDLE)

        threading.Thread(target=_worker, daemon=True).start()

    def _listen_loop(self) -> None:
        """Main listening loop — runs in background thread."""
        while not self._should_stop:
            try:
                self._root.after(0, self._set_state, STATE_LISTENING)
                self._root.after(0, self._update_transcript, "Listening...")

                audio = self._listener.listen()
                if audio is None:
                    self._root.after(0, self._set_state, STATE_IDLE)
                    continue

                self._root.after(0, self._set_state, STATE_PROCESSING)
                self._root.after(0, self._update_transcript, "Transcribing...")

                text = self._transcriber.transcribe(audio)
                if not text:
                    self._root.after(0, self._set_state, STATE_IDLE)
                    continue

                self._process_command(text)

            except Exception as exc:
                if not self._should_stop:
                    self._root.after(0, self._add_history, f"  ✗ Listener error: {exc}")
                    self._root.after(0, self._set_state, STATE_IDLE)

    def _on_close(self) -> None:
        """Handle window close."""
        self._should_stop = True
        self._root.destroy()

    def run(self) -> None:
        """Start the UI and listening loop."""
        # Start listening in background thread
        listen_thread = threading.Thread(target=self._listen_loop, daemon=True)
        listen_thread.start()

        # Run the tkinter main loop
        self._root.mainloop()
