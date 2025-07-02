import hashlib
import importlib.resources as pkg_resources
from cffi import FFI

ffi = FFI()
ffi.cdef("""
    int solve_pow(const char *nonce, int difficulty, unsigned long long *result);
""")
_lib = None


def _load_library():
    global _lib
    if _lib is None:
        lib_path = pkg_resources.files('dedi_gateway.data.bin') / 'libpow.so'
        _lib = ffi.dlopen(str(lib_path))
    return _lib


def solve(nonce: str, difficulty: int) -> int:
    """
    Solve a proof of work challenge.

    This function calls a custom C library for native acceleration of the
    SHA-256 hashing.
    :param nonce: The nonce to use for the proof of work challenge.
    :param difficulty: How many leading zeros the hash should have.
    :return:
    """
    if not isinstance(nonce, str) or not isinstance(difficulty, int):
        raise TypeError("Expected nonce: str and difficulty: int")

    res_ptr = ffi.new("unsigned long long *")
    lib = _load_library()
    ret = lib.solve_pow(nonce.encode("utf-8"), difficulty, res_ptr)

    if ret != 0:
        raise RuntimeError("PoW solving failed")

    return res_ptr[0]


def validate(nonce: str,
             difficulty: int,
             response: int,
             ) -> bool:
    """
    Validate a proof of work response.
    :param nonce: The nonce used for the proof of work challenge.
    :param difficulty: How many leading zeros the hash should have.
    :param response: The response to validate against the challenge.
    :return: True if the response is valid, False otherwise.
    """
    data = f'{nonce}{response}'.encode()
    h = hashlib.sha256(data).hexdigest()
    bin_hash = bin(int(h, 16))[2:].zfill(256)

    target = '0' * difficulty

    return bin_hash.startswith(target)
