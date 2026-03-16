# Placeholder / mock audit (no fake behaviour)

Items that were or still are stubs. Fixes applied 2026-03.

## Fixed

- **agentic_document_workflow**: Was simulated single-step mock. Now uses real `context.sample_step` loop with tool execution (FastMCP 3.1).
- **GET /api/scanners**: Was returning fake "Demo Scanner" when discovery failed. Now returns `scanners: []` and `error` message. Discovery and scan run on a single dedicated STA thread; device release no longer calls `CoUninitialize()` so subsequent discovery still sees devices.

## Remaining (non-gaslighting)

- **backend_manager.MockOCRBackend**: Used only when a backend fails to load; returns clear errors, not fake success.
- **backend/app.py demo_mode**: When `demo_mode = True`, upload/scan paths return mock results. Default is `False`; no fake data in normal run.
- **backend/app.py** (lines ~747, 866–875): In-file comments "mock for now" / "Placeholder" for quality score and some preprocessing steps; logic still runs, values may be simplified.
- **_workflow.py**: Some "placeholder" or "mock it" comments for optional features; core flows are real.
- **Tests**: Use mocks by design; not production code.

## Scanner note

WIA COM is thread-affine (STA). All discovery and scan run on a single-thread `ThreadPoolExecutor` so the same STA thread is used every time. Device release no longer calls `CoUninitialize()` (that was breaking subsequent discovery). If the flatbed is not found: check USB, Windows "Devices and Printers", and that the WIA driver is installed for the device.
