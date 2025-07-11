import sys
import hashlib
import importlib.resources as pkg_resources
from cffi import FFI

from ..consts import LOGGER

ffi = FFI()
ffi.cdef("""
    int solve_pow(const char *nonce, int difficulty, unsigned long long *result);
""")


class PowDriver:
    """
    A class to handle proof of work challenges using a native C library,
    falling back to Python implementation if the library is not available.
    """
    _lib = None

    @property
    def lib(self):
        """
        C library getter.
        :return: The Lib object from CFFI interface, pointing to the native library.
        """
        if self._lib is None:
            if sys.platform == 'win32':
                raise RuntimeError("Native library is not available on Windows")
            elif sys.platform == 'darwin':
                raise RuntimeError("Native library is not available on macOS")
            else:
                lib_name = 'libpow.so'

            lib_path = pkg_resources.files('dedi_gateway.data.bin') / lib_name
            PowDriver._lib = ffi.dlopen(str(lib_path))

        return self._lib

    def _c_solve(self, nonce: str, difficulty: int) -> int:
        """
        Solve a proof of work challenge with CFFI interface.

        This function calls a custom C library for native acceleration of the
        SHA-256 hashing.
        :param nonce: The nonce to use for the proof of work challenge.
        :param difficulty: How many leading zeros the hash should have.
        :return: The valid nonce that solves the challenge.
        """
        if not isinstance(nonce, str) or not isinstance(difficulty, int):
            raise TypeError('Expected nonce: str and difficulty: int')

        res_ptr = ffi.new('unsigned long long *')
        ret = self.lib.solve_pow(nonce.encode('utf-8'), difficulty, res_ptr)

        if ret != 0:
            raise RuntimeError('PoW solving failed')

        return res_ptr[0]

    def _python_solve(self, nonce: str, difficulty: int) -> int:
        """
        Solve a proof of work challenge with Python implementation.

        This is a fallback implementation that uses Python's hashlib
        to compute the SHA-256 hash and find a valid nonce.
        :param nonce: The nonce to use for the proof of work challenge.
        :param difficulty: How many leading zeros the hash should have.
        :return: The valid nonce that solves the challenge.
        """
        if not isinstance(nonce, str) or not isinstance(difficulty, int):
            raise TypeError('Expected nonce: str and difficulty: int')
        if difficulty < 1 or difficulty > 256:
            raise ValueError('Difficulty must be between 1 and 256')

        target_prefix = '0' * difficulty

        for counter in range(1 << 64):  # covers entire 64-bit unsigned range
            data = f"{nonce}{counter}".encode()
            digest = hashlib.sha256(data).hexdigest()
            bin_hash = bin(int(digest, 16))[2:].zfill(256)

            if bin_hash.startswith(target_prefix):
                return counter

        raise RuntimeError("No valid nonce found within 64-bit search space")

    def solve(self, nonce: str, difficulty: int) -> int:
        """
        Solve a proof of work challenge.
        :param nonce: The nonce to use for the proof of work challenge.
        :param difficulty: How many leading zeros the hash should have.
        :return: The valid nonce that solves the challenge.
        """
        try:
            return self._c_solve(nonce, difficulty)
        except OSError:
            LOGGER.exception(
                'libpow C library is not available, '
                'falling back to Python implementation.'
            )
            return self._python_solve(nonce, difficulty)

    def validate(self,
                 nonce: str,
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
