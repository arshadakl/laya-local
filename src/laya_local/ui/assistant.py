"""Voice assistant GUI built with tkinter.

Dark-themed interface with animated mic, real-time audio visualization,
transcription preview, and action result display.
"""

from __future__ import annotations

import math
import queue
import threading
import tkinter as tk
from tkinter import messagebox
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from laya_local.core.classifier import Classifier
    from laya_local.core.executor import Executor
    from laya_local.core.listener import Listener
    from laya_local.core.transcriber import Transcriber

# ── Colors ────────────────────────────────────────────────────────
_BG = "#0d1117"
_BG2 = "#161b22"
_BG3 = "#21262d"
_TEXT = "#e6edf3"
_DIM = "#8b949e"
_BLUE = "#58a6ff"
_GREEN = "#3fb950"
_RED = "#f85149"
_YELLOW = "#d29922"
_PURPLE = "#bc8cff"

# ── States ────────────────────────────────────────────────────────
IDLE = "idle"
RECORDING = "recording"
TRANSCRIBING = "transcribing"
CLASSIFYING = "classifying"
RESULT_OK = "result_ok"
RESULT_ERR = "result_err"


def tk_confirm(message: str) -> bool:
    """Ask the user to confirm a destructive action via a dialog.

    Must be called from a background thread; schedules the dialog on
    the tkinter main thread and waits for the answer.

    Args:
        message: Confirmation prompt text.

    Returns:
        True if the user confirms, False otherwise.
    """
    result_queue: queue.Queue[bool] = queue.Queue()

    root = tk._default_root  # type: ignore[attr-defined]
    if root is None:
        return False

    def _ask() -> None:
        answer = messagebox.askyesno(
            "laya-local — Confirm",
            f"{message}",
            parent=root,
        )
        result_queue.put(bool(answer))

    root.after(0, _ask)

    try:
        return result_queue.get(timeout=15)
    except queue.Empty:
        return False


class AssistantUI:
    """Voice assistant GUI with animated mic and real-time feedback.

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

        if getattr(listener, "mode", "push_to_talk") == "wake_word":
            self._idle_hint = f"Say \u201c{listener.wake_word}\u201d"
            self._status_hint = (
                f"  Say \u201c{listener.wake_word}\u201d to wake  |  Esc to quit"
            )
        else:
            self._idle_hint = "Hold right Ctrl to speak"
            self._status_hint = "  Hold right Ctrl to speak  |  Esc to quit"

        self._state = IDLE
        self._angle = 0.0
        self._stop = False

        # Audio levels for visualization (last N chunks)
        self._audio_levels: list[float] = [0.0] * 32

        # Build window
        self._root = tk.Tk()
        self._root.title("laya-local")
        self._root.geometry("520x650")
        self._root.configure(bg=_BG)
        self._root.resizable(False, False)
        self._root.protocol("WM_DELETE_WINDOW", self._on_close)

        self._build_ui()
        self._animate()

    def _build_ui(self) -> None:
        """Construct all UI elements."""
        # ── Header ────────────────────────────────────────────────
        hdr = tk.Frame(self._root, bg=_BG)
        hdr.pack(fill=tk.X, padx=20, pady=(15, 0))

        tk.Label(
            hdr, text="laya-local", font=("Segoe UI", 18, "bold"), fg=_BLUE, bg=_BG
        ).pack(side=tk.LEFT)
        tk.Label(hdr, text="v0.1.0", font=("Segoe UI", 10), fg=_DIM, bg=_BG).pack(
            side=tk.LEFT, padx=(8, 0), pady=(5, 0)
        )

        # ── Mic canvas ────────────────────────────────────────────
        self._canvas = tk.Canvas(
            self._root, width=200, height=200, bg=_BG, highlightthickness=0
        )
        self._canvas.pack(pady=(20, 5))

        # ── State label ───────────────────────────────────────────
        self._state_lbl = tk.Label(
            self._root,
            text=self._idle_hint,
            font=("Segoe UI", 14),
            fg=_DIM,
            bg=_BG,
        )
        self._state_lbl.pack(pady=(0, 10))

        # ── Audio level bars ──────────────────────────────────────
        self._bars_canvas = tk.Canvas(
            self._root, width=460, height=40, bg=_BG2, highlightthickness=0
        )
        self._bars_canvas.pack(padx=20, pady=(0, 10))

        # ── Transcript card ───────────────────────────────────────
        card1 = tk.Frame(self._root, bg=_BG2)
        card1.pack(fill=tk.X, padx=20, pady=(0, 8))

        tk.Label(
            card1,
            text="  HEARD",
            font=("Segoe UI", 9, "bold"),
            fg=_DIM,
            bg=_BG2,
            anchor="w",
        ).pack(fill=tk.X, padx=10, pady=(8, 0))

        self._heard = tk.Label(
            card1,
            text="...",
            font=("Segoe UI", 12),
            fg=_TEXT,
            bg=_BG2,
            anchor="w",
            wraplength=440,
            justify=tk.LEFT,
        )
        self._heard.pack(fill=tk.X, padx=10, pady=(4, 10))

        # ── Result card ───────────────────────────────────────────
        card2 = tk.Frame(self._root, bg=_BG2)
        card2.pack(fill=tk.X, padx=20, pady=(0, 8))

        tk.Label(
            card2,
            text="  ACTION",
            font=("Segoe UI", 9, "bold"),
            fg=_DIM,
            bg=_BG2,
            anchor="w",
        ).pack(fill=tk.X, padx=10, pady=(8, 0))

        self._action = tk.Label(
            card2,
            text="...",
            font=("Segoe UI", 12),
            fg=_GREEN,
            bg=_BG2,
            anchor="w",
            wraplength=440,
            justify=tk.LEFT,
        )
        self._action.pack(fill=tk.X, padx=10, pady=(4, 10))

        # ── History ───────────────────────────────────────────────
        hist_frame = tk.Frame(self._root, bg=_BG2)
        hist_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 8))

        tk.Label(
            hist_frame,
            text="  HISTORY",
            font=("Segoe UI", 9, "bold"),
            fg=_DIM,
            bg=_BG2,
            anchor="w",
        ).pack(fill=tk.X, padx=10, pady=(8, 0))

        self._history = tk.Text(
            hist_frame,
            font=("Consolas", 10),
            fg=_DIM,
            bg=_BG2,
            bd=0,
            highlightthickness=0,
            state=tk.DISABLED,
            height=5,
        )
        self._history.pack(fill=tk.BOTH, expand=True, padx=10, pady=(4, 8))

        # ── Status bar ────────────────────────────────────────────
        bar = tk.Frame(self._root, bg=_BG3, height=28)
        bar.pack(fill=tk.X, side=tk.BOTTOM)
        self._status = tk.Label(
            bar,
            text=self._status_hint,
            font=("Segoe UI", 9),
            fg=_DIM,
            bg=_BG3,
            anchor="w",
        )
        self._status.pack(fill=tk.X, padx=5, pady=2)

    # ── Drawing ───────────────────────────────────────────────────

    def _draw_mic(self) -> None:
        """Draw the mic indicator based on current state."""
        c = self._canvas
        c.delete("all")
        cx, cy = 100, 100

        if self._state == IDLE:
            c.create_oval(
                cx - 40, cy - 40, cx + 40, cy + 40, fill=_BG3, outline=_DIM, width=2
            )
            c.create_text(cx, cy, text="\U0001f399", font=("Segoe UI Emoji", 22))

        elif self._state == RECORDING:
            # Pulsing rings
            for i in range(3):
                r = 50 + i * 14 + int(8 * math.sin(self._angle + i * 0.9))
                c.create_oval(cx - r, cy - r, cx + r, cy + r, outline=_BLUE, width=2)
            c.create_oval(cx - 40, cy - 40, cx + 40, cy + 40, fill=_BLUE, outline=_BLUE)
            c.create_text(cx, cy, text="\U0001f399", font=("Segoe UI Emoji", 22))

        elif self._state == TRANSCRIBING:
            c.create_oval(
                cx - 40, cy - 40, cx + 40, cy + 40, fill=_BG3, outline=_YELLOW, width=2
            )
            c.create_text(
                cx, cy, text="...", font=("Segoe UI", 20, "bold"), fill=_YELLOW
            )

        elif self._state == CLASSIFYING:
            # Spinning dots
            for i in range(8):
                a = self._angle + i * math.pi / 4
                dx, dy = 55 * math.cos(a), 55 * math.sin(a)
                sz = 3 + 2 * math.sin(self._angle * 2 + i)
                c.create_oval(
                    cx + dx - sz,
                    cy + dy - sz,
                    cx + dx + sz,
                    cy + dy + sz,
                    fill=_PURPLE,
                    outline="",
                )
            c.create_oval(
                cx - 40, cy - 40, cx + 40, cy + 40, fill=_BG3, outline=_PURPLE, width=2
            )
            c.create_text(cx, cy, text="\u23f3", font=("Segoe UI Emoji", 20))

        elif self._state == RESULT_OK:
            c.create_oval(
                cx - 40, cy - 40, cx + 40, cy + 40, fill=_GREEN, outline=_GREEN
            )
            c.create_text(
                cx, cy, text="\u2713", font=("Segoe UI", 28, "bold"), fill="white"
            )

        elif self._state == RESULT_ERR:
            c.create_oval(cx - 40, cy - 40, cx + 40, cy + 40, fill=_RED, outline=_RED)
            c.create_text(
                cx, cy, text="\u2717", font=("Segoe UI", 28, "bold"), fill="white"
            )

    def _draw_bars(self) -> None:
        """Draw audio level visualization bars."""
        c = self._bars_canvas
        c.delete("all")
        w = 460
        n = len(self._audio_levels)
        bar_w = max(2, (w - n) // n)

        for i, level in enumerate(self._audio_levels):
            x = i * (bar_w + 1)
            h = max(2, int(level * 35))
            color = _BLUE if self._state == RECORDING else _BG3
            c.create_rectangle(x, 40 - h, x + bar_w, 40, fill=color, outline="")

    def _animate(self) -> None:
        """Animation tick."""
        if self._stop:
            return

        if self._state in (RECORDING, CLASSIFYING):
            self._angle += 0.18

        # Decay audio levels when not recording
        if self._state != RECORDING:
            self._audio_levels = [v * 0.85 for v in self._audio_levels]

        self._draw_mic()
        self._draw_bars()
        self._root.after(40, self._animate)

    # ── State management ──────────────────────────────────────────

    def _set_state(self, state: str) -> None:
        self._state = state
        labels = {
            IDLE: (self._idle_hint, _DIM),
            RECORDING: ("Listening...", _BLUE),
            TRANSCRIBING: ("Transcribing...", _YELLOW),
            CLASSIFYING: ("Thinking...", _PURPLE),
            RESULT_OK: ("Done!", _GREEN),
            RESULT_ERR: ("Error", _RED),
        }
        text, color = labels.get(state, ("", _DIM))
        self._state_lbl.config(text=text, fg=color)

    def _set_heard(self, text: str) -> None:
        self._heard.config(text=text)

    def _set_action(self, text: str, color: str = _GREEN) -> None:
        self._action.config(text=text, fg=color)

    def _add_history(self, line: str) -> None:
        self._history.config(state=tk.NORMAL)
        self._history.insert(tk.END, line + "\n")
        self._history.see(tk.END)
        self._history.config(state=tk.DISABLED)

    def _on_audio_chunk(self, chunk: np.ndarray) -> None:
        """Callback for real-time audio level visualization."""
        level = float(np.sqrt(np.mean(chunk.astype(np.float64) ** 2)))
        self._audio_levels.append(min(level * 10, 1.0))
        if len(self._audio_levels) > 32:
            self._audio_levels.pop(0)

    # ── Pipeline ──────────────────────────────────────────────────

    def _process(self, text: str) -> None:
        """Classify and execute a command."""

        def _worker() -> None:
            try:
                # Transcribe done — show text
                self._root.after(0, self._set_heard, text)
                self._root.after(0, self._set_state, CLASSIFYING)

                # Classify
                intent = self._classifier.classify(text)
                if intent is None:
                    msg = f"Could not understand: {text}"
                    self._root.after(0, self._set_action, msg, _YELLOW)
                    self._root.after(0, self._add_history, f"  \u26a0 {msg}")
                    self._root.after(0, self._set_state, RESULT_ERR)
                    self._root.after(2500, self._reset)
                    return

                # Execute
                result = self._executor.execute(intent)
                action = intent.get("action", "unknown")
                target = intent.get("target", "")
                status = result.get("status", "error")
                message = result.get("message", "")

                if status == "success":
                    display = f"{action} \u2192 {target}" if target else action
                    self._root.after(0, self._set_action, display, _GREEN)
                    self._root.after(
                        0, self._add_history, f"  \u2713 {text} \u2192 {display}"
                    )
                    self._root.after(0, self._set_state, RESULT_OK)
                elif status == "cancelled":
                    self._root.after(0, self._set_action, "Cancelled", _YELLOW)
                    self._root.after(
                        0, self._add_history, f"  \u26a0 {text} \u2192 cancelled"
                    )
                    self._root.after(0, self._set_state, RESULT_ERR)
                else:
                    self._root.after(0, self._set_action, message, _RED)
                    self._root.after(
                        0, self._add_history, f"  \u2717 {text} \u2192 {message}"
                    )
                    self._root.after(0, self._set_state, RESULT_ERR)

                self._root.after(2500, self._reset)

            except Exception as exc:
                msg = f"Error: {exc}"
                self._root.after(0, self._set_action, msg, _RED)
                self._root.after(0, self._add_history, f"  \u2717 {msg}")
                self._root.after(0, self._set_state, RESULT_ERR)
                self._root.after(2500, self._reset)

        threading.Thread(target=_worker, daemon=True).start()

    def _reset(self) -> None:
        """Reset to idle state."""
        self._set_state(IDLE)
        self._set_heard("...")
        self._set_action("...", _GREEN)

    def _listen_loop(self) -> None:
        """Background listening loop."""
        if self._listener.mode == "wake_word":
            listen_hint = f"Listening for \u201c{self._listener.wake_word}\u201d..."
            record_hint = "Command heard — recording..."
        else:
            listen_hint = "Listening... hold right Ctrl"
            record_hint = "Recording... release right Ctrl when done"

        while not self._stop:
            try:
                self._root.after(0, self._set_state, RECORDING)
                self._root.after(0, self._set_heard, listen_hint)

                audio = self._listener.listen(
                    on_start=lambda: self._root.after(0, self._set_heard, record_hint),
                    on_audio=self._on_audio_chunk,
                )

                if audio is None or len(audio) == 0:
                    self._root.after(0, self._reset)
                    continue

                # Got audio — transcribe
                self._root.after(0, self._set_state, TRANSCRIBING)
                self._root.after(0, self._set_heard, "Transcribing...")

                text = self._transcriber.transcribe(audio)
                if not text:
                    self._root.after(0, self._set_heard, "(no speech detected)")
                    self._root.after(2000, self._reset)
                    continue

                # Got text — process
                self._process(text)

            except Exception as exc:
                if not self._stop:
                    self._root.after(0, self._add_history, f"  \u2717 Listener: {exc}")
                    self._root.after(0, self._reset)

    def _on_close(self) -> None:
        self._stop = True
        self._root.destroy()

    def run(self) -> None:
        """Start the UI and listening loop."""
        t = threading.Thread(target=self._listen_loop, daemon=True)
        t.start()
        self._root.mainloop()
