import sys
import ctypes
import ctypes.util


# ── Seccomp (kernel-level syscall filtering) ──────────────────────────
def _apply_seccomp():
    lib_path = ctypes.util.find_library("seccomp")
    if not lib_path:
        return False
    lib = ctypes.cdll.LoadLibrary(lib_path)

    SCMP_ACT_ALLOW = 0x7FFF0000
    SCMP_ACT_ERRNO = lambda ep: 0x00050000 | (ep & 0xFFFF)
    EPERM = 1

    lib.seccomp_init.restype = ctypes.c_void_p
    lib.seccomp_init.argtypes = [ctypes.c_uint32]
    lib.seccomp_rule_add.restype = ctypes.c_int
    lib.seccomp_rule_add.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_int, ctypes.c_uint32]
    lib.seccomp_load.restype = ctypes.c_int
    lib.seccomp_load.argtypes = [ctypes.c_void_p]
    lib.seccomp_release.restype = ctypes.c_int
    lib.seccomp_release.argtypes = [ctypes.c_void_p]

    # x86_64 syscall numbers
    SOCKET = 41
    CONNECT = 42
    ACCEPT = 43
    BIND = 49
    LISTEN = 50
    SOCKETPAIR = 53
    ACCEPT4 = 288

    ctx = lib.seccomp_init(SCMP_ACT_ALLOW)
    if not ctx:
        return False

    for nr in (SOCKET, CONNECT, ACCEPT, BIND, LISTEN, SOCKETPAIR, ACCEPT4):
        lib.seccomp_rule_add(ctx, SCMP_ACT_ERRNO(EPERM), nr, 0)

    ok = lib.seccomp_load(ctx) == 0
    lib.seccomp_release(ctx)
    return ok


_has_seccomp = _apply_seccomp()

# ── Module import blocking (always active) ────────────────────────────
import builtins as _b

_orig_import = _b.__import__
_safe_import = lambda name, *args, _orig=_orig_import, _blocked={"subprocess", "ctypes", "requests"}, **kw: (
    (_ for _ in ()).throw(RuntimeError(f"Module '{name}' is blocked in sandbox"))
    if name.split(".")[0] in _blocked
    else _orig(name, *args, **kw)
)
_b.__import__ = _safe_import
del _b, _orig_import, _safe_import

# ── Python-level network fallback (when seccomp unavailable) ──────────
if not _has_seccomp:
    import _socket
    import socket

    class _NoNet:
        def __init__(self, *args, **kwargs):
            raise RuntimeError("Network access is blocked in sandbox")
        def close(self):
            pass
        def detach(self):
            raise RuntimeError("Network access is blocked in sandbox")
        def __getattr__(self, name):
            if name.startswith("_"):
                raise AttributeError(name)
            raise RuntimeError("Network access is blocked in sandbox")

    _socket.socket = _NoNet
    socket.socket = _NoNet
    socket.create_connection = lambda *a, **kw: (_ for _ in ()).throw(RuntimeError("Network blocked"))
    socket.create_server = lambda *a, **kw: (_ for _ in ()).throw(RuntimeError("Network blocked"))
    del _socket, socket, _NoNet

del _apply_seccomp, _has_seccomp

# ── Run user script ───────────────────────────────────────────────────
script = sys.argv[1]
sys.argv = sys.argv[1:]
exec(compile(open(script).read(), script, "exec"))
