#include "core.h"

#ifdef _WIN32
#include <windows.h>

int core_get_info(struct core_info *out) {
    SYSTEM_INFO si;
    WCHAR wide_host[MAX_COMPUTERNAME_LENGTH + 1];
    DWORD host_len = MAX_COMPUTERNAME_LENGTH + 1;

    if (out == NULL)
        return (int)ERROR_INVALID_PARAMETER;
    ZeroMemory(out, sizeof *out);

    GetSystemInfo(&si);
    out->pid = (int64_t)GetCurrentProcessId();
    out->cpus = (int32_t)si.dwNumberOfProcessors;
    out->page_size = (int32_t)si.dwPageSize;
    out->uptime_s = (int64_t)(GetTickCount64() / 1000);

    if (!GetComputerNameW(wide_host, &host_len))
        return (int)GetLastError();
    if (WideCharToMultiByte(CP_UTF8, 0, wide_host, -1, out->host,
                            (int)sizeof out->host, NULL, NULL) == 0)
        return (int)GetLastError();

    out->host[sizeof out->host - 1] = '\0';
    return 0;
}

#else
#include <errno.h>
#include <stddef.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

#ifdef __APPLE__
#include <sys/sysctl.h>
#include <sys/time.h>
#elif defined(__linux__)
#include <sys/sysinfo.h>
#endif

int core_get_info(struct core_info *out) {
    if (out == NULL)
        return EINVAL;
    memset(out, 0, sizeof *out);

    out->pid = (int64_t)getpid();

    long cpus = sysconf(_SC_NPROCESSORS_ONLN);
    if (cpus < 0)
        return errno ? errno : EINVAL;
    out->cpus = (int32_t)cpus;

    long page_size = sysconf(_SC_PAGESIZE);
    if (page_size < 0)
        return errno ? errno : EINVAL;
    out->page_size = (int32_t)page_size;

    if (gethostname(out->host, sizeof out->host) != 0)
        return errno;
    out->host[sizeof out->host - 1] = '\0';

#ifdef __APPLE__
    struct timeval boot_time;
    size_t boot_time_size = sizeof boot_time;
    if (sysctlbyname("kern.boottime", &boot_time, &boot_time_size, NULL, 0) != 0)
        return errno;
    time_t now = time(NULL);
    if (now == (time_t)-1 || now < boot_time.tv_sec)
        return errno ? errno : EINVAL;
    out->uptime_s = (int64_t)(now - boot_time.tv_sec);
#elif defined(__linux__)
    struct sysinfo system_info;
    if (sysinfo(&system_info) != 0)
        return errno;
    out->uptime_s = (int64_t)system_info.uptime;
#else
    return ENOTSUP;
#endif

    return 0;
}
#endif
