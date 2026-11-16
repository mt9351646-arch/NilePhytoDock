from PySide6 import QtCore
import ctypes
print(QtCore.__file__,QtCore.qVersion())
k=ctypes.windll.kernel32;k.GetModuleHandleW.restype=ctypes.c_void_p;k.GetModuleFileNameW.argtypes=[ctypes.c_void_p,ctypes.c_wchar_p,ctypes.c_uint32]
for name in ['Qt6Core.dll','icuuc.dll','msvcp140.dll']:
 h=k.GetModuleHandleW(name);buf=ctypes.create_unicode_buffer(32768);k.GetModuleFileNameW(h,buf,len(buf));print(name,buf.value)
