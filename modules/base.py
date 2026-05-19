from PyQt6.QtCore import QThread, pyqtSignal


class ScanWorker(QThread):
    """Base worker thread for all scan modules."""
    result_ready  = pyqtSignal(dict)
    log_message   = pyqtSignal(str, str)   # message, level (INFO/SUCCESS/WARNING/ERROR)
    progress      = pyqtSignal(int)        # 0-100

    def __init__(self, target: str, **kwargs):
        super().__init__()
        self.target  = target.strip()
        self.kwargs  = kwargs
        self._abort  = False

    def abort(self):
        self._abort = True

    def log(self, msg: str, level: str = "INFO"):
        self.log_message.emit(msg, level)

    def run(self):
        raise NotImplementedError("Subclass must implement run()")

    # ------------------------------------------------------------------ helpers
    @staticmethod
    def empty_result(target: str) -> dict:
        return {
            "target":      target,
            "status":      "success",
            "risk_score":  0,
            "findings":    [],
            "data":        {}
        }

    @staticmethod
    def error_result(target: str, error: str) -> dict:
        return {
            "target":     target,
            "status":     "error",
            "error":      error,
            "risk_score": 0,
            "findings":   [],
            "data":       {}
        }
