import os
import importlib.resources as pkg_resources
from cffi import FFI

ffi = FFI()

ffi.cdef("""
    int solve_pow(const char *nonce, int difficulty, unsigned long long *result);
""")

# Load and persist the shared library once
_lib = None

def _load_library():
    global _lib
    if _lib is None:
        lib_path = pkg_resources.files('dedi_gateway.data.bin') / 'libpow.so'
        _lib = ffi.dlopen(str(lib_path))
    return _lib

def solve(nonce: str, difficulty: int) -> int:
    if not isinstance(nonce, str) or not isinstance(difficulty, int):
        raise TypeError("Expected nonce: str and difficulty: int")

    res_ptr = ffi.new("unsigned long long *")
    lib = _load_library()
    ret = lib.solve_pow(nonce.encode("utf-8"), difficulty, res_ptr)

    if ret != 0:
        raise RuntimeError("PoW solving failed")

    return res_ptr[0]
