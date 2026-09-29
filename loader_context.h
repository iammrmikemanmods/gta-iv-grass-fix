#ifndef GTAIV_GRASS_LOADER_CONTEXT_H
#define GTAIV_GRASS_LOADER_CONTEXT_H

#include <windows.h>

typedef BYTE (WINAPI *GuRtlIsThreadWithinLoaderCalloutFn)(void);
typedef LONG (WINAPI *GuNtQueryInformationProcessFn)(
    HANDLE, DWORD, void *, DWORD, DWORD *);
typedef BOOL (WINAPI *GuRtlIsCriticalSectionLockedByThreadFn)(
    CRITICAL_SECTION *);

struct GuProcessBasicInformation32 {
    LONG exit_status;
    BYTE *peb;
    DWORD affinity;
    LONG priority;
    DWORD process_id;
    DWORD parent_process_id;
};

/* Wine's x86 PEB.LoaderLock is at 0xa0 (include/winternl.h).
 * Check ownership: a recursive try-lock would also succeed inside DllMain.
 */
static BOOL gu_loader_can_wait(void)
{
    HMODULE ntdll = GetModuleHandleA("ntdll.dll");
    GuRtlIsThreadWithinLoaderCalloutFn in_callout;
    GuNtQueryInformationProcessFn query_process;
    GuRtlIsCriticalSectionLockedByThreadFn owns_lock;
    struct GuProcessBasicInformation32 info;
    CRITICAL_SECTION *loader_lock = NULL;
    CRITICAL_SECTION snapshot;
    DWORD returned = 0u;
    SIZE_T copied = 0u;

    if (!ntdll) {
        return FALSE;
    }
    in_callout = (GuRtlIsThreadWithinLoaderCalloutFn)GetProcAddress(
        ntdll, "RtlIsThreadWithinLoaderCallout");
    if (in_callout) {
        return !in_callout();
    }
    if (sizeof(void *) != 4u || sizeof(info) != 24u ||
        sizeof(snapshot) != 24u ||
        !GetProcAddress(ntdll, "wine_get_version")) {
        return FALSE;
    }
    query_process = (GuNtQueryInformationProcessFn)GetProcAddress(
        ntdll, "NtQueryInformationProcess");
    owns_lock = (GuRtlIsCriticalSectionLockedByThreadFn)GetProcAddress(
        ntdll, "RtlIsCriticalSectionLockedByThread");
    if (!query_process || !owns_lock ||
        query_process(GetCurrentProcess(), 0u, &info, sizeof(info),
                      &returned) != 0 || returned != sizeof(info) ||
        !info.peb || info.process_id != GetCurrentProcessId()) {
        return FALSE;
    }
    if (!ReadProcessMemory(GetCurrentProcess(), info.peb + 0xa0u,
                           &loader_lock, sizeof(loader_lock), &copied) ||
        copied != sizeof(loader_lock) || !loader_lock ||
        !ReadProcessMemory(GetCurrentProcess(), loader_lock, &snapshot,
                           sizeof(snapshot), &copied) ||
        copied != sizeof(snapshot)) {
        return FALSE;
    }
    return !owns_lock(loader_lock);
}

#endif
