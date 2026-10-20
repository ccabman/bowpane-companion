"""Isolated, redacted module health. Adapters are internal read-only callables."""
import asyncio
import inspect

MODULES = ("photos", "calendars", "music")
STATES = {"healthy", "syncing", "waiting_for_mac", "permission_required",
          "reauthentication_required", "stale", "unsupported", "error"}
REASONS = {"adapter_not_connected", "permission_required", "reauthentication_required",
           "waiting_for_mac", "sync_in_progress", "no_successful_sync", "stale",
           "adapter_error", "adapter_timeout"}


def record(state="unsupported", reason="adapter_not_connected"):
    return {"state": state, "reason": reason, "lastAttempt": None, "lastSuccess": None}


async def module_health(collector):
    if collector is None:
        return record()
    try:
        # Require asynchronous adapters so blocking I/O cannot run in the loop.
        if not inspect.iscoroutinefunction(collector):
            return record("error", "adapter_error")
        async with asyncio.timeout(1):
            result = await collector()
        if not isinstance(result, dict) or result.get("state") not in STATES or result.get("reason") not in REASONS:
            return record("error", "adapter_error")
        # Never reflect exception text, arbitrary strings or household content.
        # Sync timestamps and metadata require a separate validated schema later.
        return record(result["state"], result["reason"])
    except TimeoutError:
        return record("error", "adapter_timeout")
    except Exception:  # noqa: BLE001 — isolate adapters; never expose exception details.
        return record("error", "adapter_error")


async def health(collectors=None):
    collectors = collectors or {}
    results = await asyncio.gather(*(module_health(collectors.get(name)) for name in MODULES))
    return {"protocolVersion": 2, "modules": dict(zip(MODULES, results))}
