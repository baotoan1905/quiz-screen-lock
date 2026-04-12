"""
keyboard_hook.py — Low-level keyboard hook for Windows.
Suppresses Escape, Win keys, and Alt+F4 while the lock screen is active.
Uses ctypes to install a WH_KEYBOARD_LL hook.

NOTE: This module only functions on Windows. On other platforms the
      install/uninstall calls are no-ops so the rest of the app can
      still be imported for development/testing on macOS/Linux.
"""
from __future__ import annotations

import ctypes
import ctypes.wintypes
import sys
import threading
from typing import Callable, Optional

BLOCKED = False          # set to True while lock screen is up
_hook_id: Optional[int] = None
_hook_thread: Optional[threading.Thread] = None

# Virtual-key codes to suppress when locked
_VK_LWIN   = 0x5B
_VK_RWIN   = 0x5C
_VK_ESCAPE = 0x1B
_VK_F4     = 0x73
_WM_KEYDOWN    = 0x0100
_WM_SYSKEYDOWN = 0x0104
_WH_KEYBOARD_LL = 13


def _is_windows() -> bool:
    return sys.platform == "win32"


if _is_windows():
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32

    HOOKPROC = ctypes.WINFUNCTYPE(
        ctypes.c_int,
        ctypes.c_int,
        ctypes.wintypes.WPARAM,
        ctypes.wintypes.LPARAM,
    )

    class _KBDLLHOOKSTRUCT(ctypes.Structure):
        _fields_ = [
            ("vkCode",      ctypes.wintypes.DWORD),
            ("scanCode",    ctypes.wintypes.DWORD),
            ("flags",       ctypes.wintypes.DWORD),
            ("time",        ctypes.wintypes.DWORD),
            ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
        ]

    def _low_level_handler(nCode: int, wParam: int, lParam: int) -> int:
        if nCode >= 0 and BLOCKED:
            kb = ctypes.cast(lParam, ctypes.POINTER(_KBDLLHOOKSTRUCT)).contents
            vk = kb.vkCode
            # Block Win keys always
            if vk in (_VK_LWIN, _VK_RWIN):
                return 1
            # Block Escape
            if vk == _VK_ESCAPE:
                return 1
            # Block Alt+F4
            if wParam in (_WM_KEYDOWN, _WM_SYSKEYDOWN) and vk == _VK_F4:
                if kb.flags & 0x20:   # LLKHF_ALTDOWN
                    return 1
        return user32.CallNextHookEx(None, nCode, wParam, lParam)

    _CALLBACK = HOOKPROC(_low_level_handler)

    def _message_loop() -> None:
        global _hook_id
        _hook_id = user32.SetWindowsHookExW(
            _WH_KEYBOARD_LL,
            _CALLBACK,
            kernel32.GetModuleHandleW(None),
            0,
        )
        msg = ctypes.wintypes.MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))
        if _hook_id:
            user32.UnhookWindowsHookEx(_hook_id)
            _hook_id = None

else:
    # Stub for non-Windows environments
    def _message_loop() -> None:
        pass


def install() -> None:
    """Start the keyboard hook in a background thread."""
    global _hook_thread
    if not _is_windows():
        return
    if _hook_thread and _hook_thread.is_alive():
        return
    _hook_thread = threading.Thread(target=_message_loop, daemon=True)
    _hook_thread.start()


def uninstall() -> None:
    """Stop blocking keys (does NOT stop the hook thread — it stays resident)."""
    global BLOCKED
    BLOCKED = False


def lock() -> None:
    """Enable key suppression (call when lock screen appears)."""
    global BLOCKED
    install()
    BLOCKED = True


def unlock() -> None:
    """Disable key suppression (call when lock screen dismisses)."""
    global BLOCKED
    BLOCKED = False
