import syslog
import inspect

def log_syslog(msg, priority='LOG_INFO', facility='LOCAL0', debug=False):
    """
    Configure syslog (/etc/rsyslog.conf) to have the following:-

    local0.*        /var/log/local0
    local1.*        /var/log/local1

    TODOS:
    Get the class name if the caller is a class/instance method 
    instead of function.
    """
    priorities = {
        'LOG_INFO': syslog.LOG_INFO,
        'LOG_WARNING': syslog.LOG_WARNING,
    }

    facilities = {
        'LOCAL0': syslog.LOG_LOCAL0,
        'LOCAL1': syslog.LOG_LOCAL1,
    }

    try:
        frame = inspect.stack()[2]
        frame_info = inspect.getframeinfo(frame[0])
        mod = inspect.getmodule(frame[0])
        filename, lineno, function, code_context, index = frame_info
    finally:
        del frame
        del frame_info

    syslog.openlog('%s.%s()' % (mod.__name__, function.strip()), 0, facilities[facility])
    if debug:
        msg = '%s %s:%s' % (msg, filename, lineno)
    syslog.syslog(priorities[priority], msg)

def info(msg, facility='LOCAL0', debug=False):
    log_syslog(msg, priority='LOG_INFO', facility=facility)

def warning(msg, facility='LOCAL0', debug=False):
    log_syslog(msg, priority='LOG_WARNING', facility=facility)
