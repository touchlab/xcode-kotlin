import sys
import os

logging = False
exe_logging = os.getenv('GLOG_log_dir') is not None


def log(msg):
    if logging:
        sys.stderr.write(msg())
        sys.stderr.write('\n')
    exelog(msg)


def exelog(stmt):
    if exe_logging:
        f = open(os.getenv('GLOG_log_dir', '') + "/konan_lldb.log", "a")
        f.write(stmt())
        f.write("\n")
        f.close()
