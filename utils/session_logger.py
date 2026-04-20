import time
import threading
from typing import Callable, List

class LogLevel:
  LOG = "LOG"
  WARNING = "WARNING"
  ERROR = "ERROR"

class LogEntry:
  def __init__(self, level: str, message: str):
    self.level = level
    self.message = message
    self.timestamp = time.strftime("%H:%M:%S")

class SessionLogger:
  """
  Thread-safe logging system using the Observer pattern.
  """
  def __init__(self, max_history: int = 1000):
    self.logs: List[LogEntry] = []
    self.max_history = max_history
    self.listeners: List[Callable[[LogEntry], None]] = []
    self.lock = threading.Lock()

  def add_listener(self, listener: Callable[[LogEntry], None]):
    """Adds a function that will be called whenever a new log is created."""
    with self.lock:
      self.listeners.append(listener)

  def _emit(self, entry: LogEntry):
    for listener in self.listeners:
      listener(entry)

  def log(self, message: str):
    self._add_log(LogEntry(LogLevel.LOG, message))

  def warning(self, message: str):
    self._add_log(LogEntry(LogLevel.WARNING, message))

  def error(self, message: str):
    self._add_log(LogEntry(LogLevel.ERROR, message))

  def _add_log(self, entry: LogEntry):
    with self.lock:
      self.logs.append(entry)
      # Cap internal memory history
      if len(self.logs) > self.max_history:
        self.logs.pop(0)
      self._emit(entry)