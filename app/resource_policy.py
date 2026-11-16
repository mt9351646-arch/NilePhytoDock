"""Conservative workstation budgets; search accuracy parameters are unchanged."""
import os

def cpu_budget():
    available=len(os.sched_getaffinity(0)) if hasattr(os,'sched_getaffinity') else (os.cpu_count() or 1)
    return max(1,min(2,available//2))

def configure_environment():
    # Must run before NumPy/OpenBLAS/Qt imports, including frozen startup.
    for name in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS','VECLIB_MAXIMUM_THREADS','BLIS_NUM_THREADS'):
        os.environ[name]='1'
    os.environ['OMP_WAIT_POLICY']='PASSIVE'

def java_heap_mb():
    import psutil
    memory=psutil.virtual_memory()
    # Leave memory for Windows, Qt and other applications; fail visibly if the
    # selected receptor cannot fit rather than paging the whole workstation.
    return max(256,min(1024,int(min(memory.total/8,memory.available/4)/1024**2)))

