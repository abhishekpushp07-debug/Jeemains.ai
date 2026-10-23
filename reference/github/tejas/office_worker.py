"""Single-process trusted launcher for a disposable, non-root office jail.
No application paths, environment secrets, network or host proc filesystem enter the jail.
"""
import ctypes, ctypes.util, errno, os, resource, sys

def main():
    root, extension = sys.argv[1:3]
    if extension not in ('doc','docx','xls','xlsx'):
        raise SystemExit(2)
    sec = ctypes.CDLL(ctypes.util.find_library('seccomp'))
    sec.seccomp_init.argtypes=[ctypes.c_uint32];sec.seccomp_init.restype=ctypes.c_void_p
    sec.seccomp_syscall_resolve_name.argtypes=[ctypes.c_char_p];sec.seccomp_syscall_resolve_name.restype=ctypes.c_int
    sec.seccomp_rule_add.argtypes=[ctypes.c_void_p,ctypes.c_uint32,ctypes.c_int,ctypes.c_uint]
    sec.seccomp_load.argtypes=[ctypes.c_void_p];sec.seccomp_release.argtypes=[ctypes.c_void_p]
    ctx=sec.seccomp_init(0x7fff0000)
    for call in ('socket','socketpair','connect','bind','listen','accept','accept4','mount','umount2','ptrace','unshare','setns','bpf','keyctl','userfaultfd'):
        number=sec.seccomp_syscall_resolve_name(call.encode())
        if number>=0 and sec.seccomp_rule_add(ctx,0x00050000|errno.EPERM,number,0)!=0:
            raise SystemExit(3)
    resource.setrlimit(resource.RLIMIT_CPU,(45,45))
    resource.setrlimit(resource.RLIMIT_AS,(1600*1024*1024,1600*1024*1024))
    resource.setrlimit(resource.RLIMIT_FSIZE,(64*1024*1024,64*1024*1024))
    resource.setrlimit(resource.RLIMIT_NOFILE,(256,256))
    resource.setrlimit(resource.RLIMIT_NPROC,(64,64))
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    os.chroot(root);os.chdir('/work');os.setgroups([]);os.setgid(65534);os.setuid(65534)
    libc=ctypes.CDLL(None)
    if libc.prctl(38,1,0,0,0)!=0 or sec.seccomp_load(ctx)!=0:
        raise SystemExit(4)
    sec.seccomp_release(ctx)
    env={'HOME':'/work','TMPDIR':'/work/tmp','PATH':'/usr/lib/libreoffice/program:/usr/bin:/bin',
         'LD_LIBRARY_PATH':'/usr/lib/libreoffice/program','LC_ALL':'C.UTF-8','TZ':'UTC','SAL_USE_VCLPLUGIN':'svp'}
    binary='/usr/lib/libreoffice/program/soffice.bin'
    args=[binary,'--headless','--nologo','--nodefault','--norestore','--nolockcheck',
          '-env:UserInstallation=file:///work/profile','--convert-to','pdf','--outdir','/work/out','/input/source.'+extension]
    os.execve(binary,args,env)

if __name__=='__main__':main()
