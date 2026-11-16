import hashlib
import json
import os
import subprocess
import threading
import time
import tempfile
from contextlib import contextmanager
from pathlib import Path
from app.paths import resource
from app.resource_policy import cpu_budget,java_heap_mb

_local=threading.local()

def current_runner():return getattr(_local,'runner',None)

@contextmanager
def task_context(runner):
    previous=current_runner();_local.runner=runner
    try:yield
    finally:_local.runner=previous

def checkpoint():
    active=current_runner()
    if active:active.checkpoint()

class _WindowsJob:
    """Own only this engine and its descendants; closing also handles crashes."""
    def __init__(self,proc):
        self.handle=None
        if os.name!='nt':return
        import ctypes
        from ctypes import wintypes as w
        class Basic(ctypes.Structure):
            _fields_=[('ProcessTime',ctypes.c_int64),('JobTime',ctypes.c_int64),('Flags',w.DWORD),('MinWorking',ctypes.c_size_t),('MaxWorking',ctypes.c_size_t),('ActiveProcesses',w.DWORD),('Affinity',ctypes.c_size_t),('Priority',w.DWORD),('Scheduling',w.DWORD)]
        class IO(ctypes.Structure):_fields_=[(n,ctypes.c_uint64) for n in ('ReadOps','WriteOps','OtherOps','ReadBytes','WriteBytes','OtherBytes')]
        class Extended(ctypes.Structure):_fields_=[('Basic',Basic),('IO',IO),('ProcessMemory',ctypes.c_size_t),('JobMemory',ctypes.c_size_t),('PeakProcessMemory',ctypes.c_size_t),('PeakJobMemory',ctypes.c_size_t)]
        api=ctypes.WinDLL('kernel32',use_last_error=True)
        api.CreateJobObjectW.argtypes=[ctypes.c_void_p,w.LPCWSTR];api.CreateJobObjectW.restype=w.HANDLE
        api.SetInformationJobObject.argtypes=[w.HANDLE,ctypes.c_int,ctypes.c_void_p,w.DWORD]
        api.AssignProcessToJobObject.argtypes=[w.HANDLE,w.HANDLE];api.CloseHandle.argtypes=[w.HANDLE]
        handle=api.CreateJobObjectW(None,None);info=Extended();info.Basic.Flags=0x2000
        if handle and api.SetInformationJobObject(handle,9,ctypes.byref(info),ctypes.sizeof(info)) and api.AssignProcessToJobObject(handle,w.HANDLE(int(proc._handle))):self.handle=handle;self.api=api
        elif handle:api.CloseHandle(handle)
    def close(self):
        if self.handle:self.api.CloseHandle(self.handle);self.handle=None

class Cancelled(RuntimeError): pass

class Runner:
    def __init__(self, cancelled=None, paused=None):
        owner=current_runner()
        self.cancelled=cancelled if cancelled is not None else owner.cancelled if owner else threading.Event()
        self.paused=paused if paused is not None else owner.paused if owner else threading.Event()

    def checkpoint(self):
        if self.cancelled.is_set(): raise Cancelled("Calculation cancelled by user")
        while self.paused.is_set():
            if self.cancelled.wait(.2): raise Cancelled("Calculation cancelled by user")

    def run(self, args, log, cwd=None, timeout=3600, env=None):
        self.checkpoint(); log=Path(log);log.parent.mkdir(parents=True,exist_ok=True)
        start=time.monotonic()
        with log.open("w",encoding="utf-8") as out:
            out.write(json.dumps([str(a) for a in args],ensure_ascii=False)+"\n");out.flush()
            child_env=os.environ.copy();child_env.update(env or {})
            for name in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):child_env[name]='1'
            flags=(subprocess.CREATE_NO_WINDOW|subprocess.BELOW_NORMAL_PRIORITY_CLASS) if os.name=='nt' else 0
            proc=subprocess.Popen([str(a) for a in args],stdout=out,stderr=subprocess.STDOUT,cwd=cwd,env=child_env,creationflags=flags)
            job=_WindowsJob(proc)
            try:
                import psutil
                try:
                    process=psutil.Process(proc.pid)
                    if os.name=='nt':process.cpu_affinity(process.cpu_affinity()[:cpu_budget()])
                except psutil.NoSuchProcess:pass
                while proc.poll() is None:
                    if self.cancelled.wait(.15): raise Cancelled("Calculation cancelled by user")
                    if time.monotonic()-start>timeout: raise TimeoutError(f"Process exceeded {timeout} seconds; see {log}")
            except BaseException:
                # Job close covers grandchildren too. Portable fallback is
                # scoped to this exact owned process tree, never executable names.
                job.close()
                try:
                    children=psutil.Process(proc.pid).children(recursive=True)
                    for child in reversed(children):
                        try:child.kill()
                        except psutil.Error:pass
                except psutil.Error:pass
                if proc.poll() is None:proc.kill()
                proc.wait();raise
            finally:job.close()
        if proc.returncode:
            raise RuntimeError(f"Engine returned {proc.returncode}. {log.read_text(encoding='utf-8',errors='replace')[-3000:]}")
        return time.monotonic()-start

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

@contextmanager
def ascii_workdir(prefix='nile_engine_'):
    with tempfile.TemporaryDirectory(prefix=prefix) as name:
        path=Path(name)
        if not str(path).isascii() and os.name=='nt':
            import ctypes
            buffer=ctypes.create_unicode_buffer(32768)
            if ctypes.windll.kernel32.GetShortPathNameW(str(path),buffer,len(buffer)):path=Path(buffer.value)
        if not str(path).isascii():raise ValueError('Native engines require an ASCII-compatible Windows temporary/short path')
        yield path

def smina(): return resource("external_tools","smina","smina.exe")
def java(): return resource("external_tools","java_runtime","bin","java.exe")
def p2rank_args():
    home=resource("external_tools","p2rank")
    return [java(),f"-Xmx{java_heap_mb()}m",f'-XX:ActiveProcessorCount={cpu_budget()}','-XX:+UseSerialGC',"-cp",str(home/"bin/p2rank.jar")+os.pathsep+str(home/"bin/lib/*"),"cz.siret.prank.program.Main"]

def health():
    checks={}
    for name,args in [("Smina",[smina(),"--version"]),("Java",[java(),"-version"]),("P2Rank",p2rank_args()+["-version"])]:
        try:
            with ascii_workdir('nile_health_') as folder:
                log=folder/'engine.log';Runner().run(args,log,timeout=30)
                output='\n'.join(log.read_text(encoding='utf-8',errors='replace').splitlines()[1:]).strip()
            checks[name]={"ok":bool(output),"version":output[:600]}
        except Cancelled:raise
        except Exception as e: checks[name]={"ok":False,"version":str(e)}
    import importlib.metadata as md
    for name in ["rdkit","prolif","PySide6","openbabel-wheel"]:
        try: checks[name]={"ok":True,"version":md.version(name)}
        except md.PackageNotFoundError: checks[name]={"ok":False,"version":"Package metadata unavailable"}
    return checks

