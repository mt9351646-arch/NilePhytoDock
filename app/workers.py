import traceback
from PySide6.QtCore import QThread,Signal
from scientific.runtime import Runner,Cancelled,task_context

class Task(QThread):
    message=Signal(str,int,int)
    succeeded=Signal(object)
    failed=Signal(str)
    cancelled=Signal()
    def __init__(self,fn,parent=None,runner=None):
        super().__init__(parent);self.fn=fn;self.runner=runner or Runner()
    def cancel(self):self.runner.cancelled.set();self.requestInterruption()
    def run(self):
        try:
            with task_context(self.runner):
                self.runner.checkpoint();result=self.fn(self.message.emit);self.runner.checkpoint()
            self.succeeded.emit(result)
        except Cancelled:self.cancelled.emit()
        except Exception as e:self.failed.emit(f'{type(e).__name__}: {e}')

