"""Windows DPAPI, šifrování pro aktuální účet. Žádné tajné hodnoty ve výstupu."""
import ctypes
from ctypes import wintypes

class Blob(ctypes.Structure):
    _fields_=[("size",wintypes.DWORD),("data",ctypes.POINTER(ctypes.c_ubyte))]

def protect(raw,decrypt=False):
    buf=(ctypes.c_ubyte*len(raw)).from_buffer_copy(raw)
    before=Blob(len(raw),buf);after=Blob()
    lib=ctypes.windll.crypt32
    func=lib.CryptUnprotectData if decrypt else lib.CryptProtectData
    if not func(ctypes.byref(before),None,None,None,None,1,ctypes.byref(after)):
        raise OSError("Účet Windows nemůže odemknout publikační údaje.")
    try:return ctypes.string_at(after.data,after.size)
    finally:ctypes.windll.kernel32.LocalFree(after.data)
