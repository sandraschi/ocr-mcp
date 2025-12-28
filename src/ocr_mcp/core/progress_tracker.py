"""
OCR-MCP Progress Tracking System

Provides real-time progress tracking for long-running OCR operations,
batch processing, and multi-document workflows.
"""

import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Callable
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)


class ProgressStatus(Enum):
    """Progress operation status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class OperationType(Enum):
    """Types of operations being tracked"""
    SINGLE_DOCUMENT = "single_document"
    BATCH_PROCESSING = "batch_processing"
    MULTI_PAGE_DOCUMENT = "multi_page_document"
    SCANNER_OPERATION = "scanner_operation"
    MODEL_LOADING = "model_loading"
    IMAGE_PREPROCESSING = "image_preprocessing"


@dataclass
class ProgressUpdate:
    """Individual progress update"""
    operation_id: str
    timestamp: float
    status: ProgressStatus
    progress: float  # 0.0 to 1.0
    current_step: str
    total_steps: int
    current_step_index: int
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    estimated_time_remaining: Optional[float] = None  # seconds


@dataclass
class OperationProgress:
    """Complete operation progress tracking"""
    operation_id: str
    operation_type: OperationType
    status: ProgressStatus
    start_time: float
    end_time: Optional[float] = None
    total_items: int = 0
    completed_items: int = 0
    failed_items: int = 0
    current_item: Optional[str] = None
    progress: float = 0.0
    current_step: str = ""
    steps: List[str] = field(default_factory=list)
    updates: List[ProgressUpdate] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def duration(self) -> float:
        """Get operation duration in seconds"""
        end_time = self.end_time or time.time()
        return end_time - self.start_time

    def estimated_completion_time(self) -> Optional[float]:
        """Estimate completion time based on current progress"""
        if self.progress <= 0:
            return None

        elapsed = self.duration()
        if elapsed <= 0:
            return None

        total_estimated = elapsed / self.progress
        return self.start_time + total_estimated


class ProgressTracker:
    """Central progress tracking system"""

    def __init__(self, max_history: int = 1000):
        self.operations: Dict[str, OperationProgress] = {}
        self.callbacks: Dict[str, List[Callable]] = {}
        self.max_history = max_history
        self._executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="progress")

    def start_operation(
        self,
        operation_type: OperationType,
        total_items: int = 1,
        steps: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Start tracking a new operation"""

        operation_id = str(uuid.uuid4())
        operation = OperationProgress(
            operation_id=operation_id,
            operation_type=operation_type,
            status=ProgressStatus.RUNNING,
            start_time=time.time(),
            total_items=total_items,
            steps=steps or [],
            metadata=metadata or {}
        )

        self.operations[operation_id] = operation

        # Clean up old operations if needed
        if len(self.operations) > self.max_history:
            # Remove oldest completed operations
            completed_ops = [
                op_id for op_id, op in self.operations.items()
                if op.status in [ProgressStatus.COMPLETED, ProgressStatus.FAILED, ProgressStatus.CANCELLED]
            ]
            for op_id in completed_ops[:len(self.operations) - self.max_history + 100]:
                del self.operations[op_id]

        logger.info(f"Started operation {operation_id} ({operation_type.value})")
        return operation_id

    def update_progress(
        self,
        operation_id: str,
        progress: float,
        message: str,
        current_step: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Update operation progress"""

        if operation_id not in self.operations:
            logger.warning(f"Unknown operation ID: {operation_id}")
            return

        operation = self.operations[operation_id]

        # Update operation state
        operation.progress = max(0.0, min(1.0, progress))
        operation.current_step = current_step or operation.current_step

        # Create progress update
        update = ProgressUpdate(
            operation_id=operation_id,
            timestamp=time.time(),
            status=operation.status,
            progress=operation.progress,
            current_step=operation.current_step,
            total_steps=len(operation.steps),
            current_step_index=operation.steps.index(operation.current_step) if operation.current_step in operation.steps else -1,
            message=message,
            details=details or {},
            estimated_time_remaining=self._estimate_time_remaining(operation)
        )

        operation.updates.append(update)

        # Notify callbacks
        self._notify_callbacks(operation_id, update)

        logger.debug(f"Progress update for {operation_id}: {progress:.1%} - {message}")

    def update_item_progress(
        self,
        operation_id: str,
        completed_items: int,
        current_item: Optional[str] = None,
        failed_items: int = 0
    ):
        """Update progress for multi-item operations"""

        if operation_id not in self.operations:
            return

        operation = self.operations[operation_id]
        operation.completed_items = completed_items
        operation.failed_items = failed_items
        operation.current_item = current_item

        if operation.total_items > 0:
            progress = (completed_items + failed_items) / operation.total_items
            operation.progress = min(1.0, progress)

            message = f"Processed {completed_items}/{operation.total_items} items"
            if failed_items > 0:
                message += f" ({failed_items} failed)"

            if current_item:
                message += f" - Current: {current_item}"

            self.update_progress(operation_id, operation.progress, message)

    def complete_operation(self, operation_id: str, success: bool = True, error_message: Optional[str] = None):
        """Mark operation as completed"""

        if operation_id not in self.operations:
            return

        operation = self.operations[operation_id]
        operation.end_time = time.time()
        operation.status = ProgressStatus.COMPLETED if success else ProgressStatus.FAILED

        if error_message:
            self.update_progress(operation_id, operation.progress, f"Failed: {error_message}")
        else:
            self.update_progress(operation_id, 1.0, "Operation completed successfully")

        logger.info(f"Completed operation {operation_id} in {operation.duration():.2f}s (success: {success})")

    def cancel_operation(self, operation_id: str, reason: str = "Cancelled by user"):
        """Cancel an operation"""

        if operation_id not in self.operations:
            return

        operation = self.operations[operation_id]
        operation.end_time = time.time()
        operation.status = ProgressStatus.CANCELLED

        self.update_progress(operation_id, operation.progress, f"Cancelled: {reason}")
        logger.info(f"Cancelled operation {operation_id}: {reason}")

    def get_operation_status(self, operation_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of an operation"""

        if operation_id not in self.operations:
            return None

        operation = self.operations[operation_id]

        return {
            "operation_id": operation_id,
            "operation_type": operation.operation_type.value,
            "status": operation.status.value,
            "progress": operation.progress,
            "start_time": operation.start_time,
            "duration": operation.duration(),
            "estimated_completion": operation.estimated_completion_time(),
            "current_step": operation.current_step,
            "total_items": operation.total_items,
            "completed_items": operation.completed_items,
            "failed_items": operation.failed_items,
            "current_item": operation.current_item,
            "metadata": operation.metadata
        }

    def list_operations(self, status_filter: Optional[List[ProgressStatus]] = None) -> List[Dict[str, Any]]:
        """List all operations with optional status filter"""

        operations = []
        for operation in self.operations.values():
            if status_filter and operation.status not in status_filter:
                continue

            operations.append(self.get_operation_status(operation.operation_id))

        # Sort by start time (newest first)
        operations.sort(key=lambda x: x["start_time"], reverse=True)
        return operations

    def add_callback(self, operation_id: str, callback: Callable[[ProgressUpdate], None]):
        """Add a callback for progress updates"""

        if operation_id not in self.callbacks:
            self.callbacks[operation_id] = []
        self.callbacks[operation_id].append(callback)

    def remove_callbacks(self, operation_id: str):
        """Remove all callbacks for an operation"""

        if operation_id in self.callbacks:
            del self.callbacks[operation_id]

    def _notify_callbacks(self, operation_id: str, update: ProgressUpdate):
        """Notify all callbacks for an operation"""

        if operation_id not in self.callbacks:
            return

        for callback in self.callbacks[operation_id]:
            try:
                # Run callback in thread pool to avoid blocking
                self._executor.submit(callback, update)
            except Exception as e:
                logger.error(f"Error in progress callback: {e}")

    def _estimate_time_remaining(self, operation: OperationProgress) -> Optional[float]:
        """Estimate time remaining for operation completion"""

        if operation.progress <= 0 or operation.progress >= 1.0:
            return None

        elapsed = operation.duration()
        if elapsed <= 0:
            return None

        # Estimate total time based on current progress
        total_estimated = elapsed / operation.progress
        remaining = total_estimated - elapsed

        return max(0, remaining)

    async def cleanup_old_operations(self, max_age_seconds: int = 3600):
        """Clean up old completed operations"""

        current_time = time.time()
        to_remove = []

        for operation_id, operation in self.operations.items():
            if (operation.status in [ProgressStatus.COMPLETED, ProgressStatus.FAILED, ProgressStatus.CANCELLED]
                and current_time - operation.end_time > max_age_seconds):
                to_remove.append(operation_id)

        for operation_id in to_remove:
            del self.operations[operation_id]
            self.remove_callbacks(operation_id)

        if to_remove:
            logger.info(f"Cleaned up {len(to_remove)} old operations")


# Global progress tracker instance
progress_tracker = ProgressTracker()


def create_progress_context(
    operation_type: OperationType,
    total_items: int = 1,
    steps: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None
):
    """Context manager for progress tracking"""

    class ProgressContext:
        def __init__(self, operation_type, total_items, steps, metadata):
            self.operation_type = operation_type
            self.total_items = total_items
            self.steps = steps
            self.metadata = metadata
            self.operation_id = None

        def __enter__(self):
            self.operation_id = progress_tracker.start_operation(
                self.operation_type, self.total_items, self.steps, self.metadata
            )
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            if exc_type:
                progress_tracker.complete_operation(self.operation_id, success=False, error_message=str(exc_val))
            else:
                progress_tracker.complete_operation(self.operation_id, success=True)

        def update_progress(self, progress: float, message: str, **kwargs):
            progress_tracker.update_progress(self.operation_id, progress, message, **kwargs)

        def update_item_progress(self, completed: int, current_item: Optional[str] = None, failed: int = 0):
            progress_tracker.update_item_progress(self.operation_id, completed, current_item, failed)

    return ProgressContext(operation_type, total_items, steps, metadata)


async def track_async_operation(
    operation_type: OperationType,
    operation_func: Callable,
    *args,
    total_items: int = 1,
    steps: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    **kwargs
):
    """Track progress for an async operation"""

    operation_id = progress_tracker.start_operation(operation_type, total_items, steps, metadata)

    try:
        # Create a wrapper function that updates progress
        async def progress_wrapper(*args, **kwargs):
            # This would be called by the operation function to report progress
            return await operation_func(*args, **kwargs)

        result = await progress_wrapper(*args, **kwargs)
        progress_tracker.complete_operation(operation_id, success=True)
        return result

    except Exception as e:
        progress_tracker.complete_operation(operation_id, success=False, error_message=str(e))
        raise