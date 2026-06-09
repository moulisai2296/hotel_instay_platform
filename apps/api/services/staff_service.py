"""Staff actions on requests (status transitions). Writes go through the API
with the service role (RLS bypassed), so hotel + department isolation is enforced
here in app code from the staff JWT context — never from the request body.

Kept separate from ``RequestService`` (the guest chat pipeline) because it needs
no AI collaborator; this is pure data access + an audit event.
"""

import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from middleware import RequestContext, assert_hotel_access
from models import Request, RequestEvent
from models.base import RequestStatus

# Roles whose view (and therefore actions) are scoped to a single department.
_DEPT_SCOPED_ROLES = frozenset({"staff", "dept_manager"})


class StaffRequestService:
    """Status transitions on requests, scoped to the acting staff member."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def update_status(
        self,
        ctx: RequestContext,
        request_id: uuid.UUID,
        new_status: RequestStatus,
        note: str | None = None,
    ) -> Request:
        """Move a request to ``new_status`` + append an audit event.

        Guards: the request must belong to the staff member's hotel, and for
        department-scoped roles (staff / dept_manager) to their department too —
        mirroring the RLS read policy so the API can't be used to reach past it.
        """
        request = await self.db.get(Request, request_id)
        if request is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Request not found",
                headers={"X-Error-Code": "NOT_FOUND"},
            )

        assert_hotel_access(ctx, request.hotel_id)
        if (
            ctx.app_role in _DEPT_SCOPED_ROLES
            and request.department_id != ctx.department_id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Request belongs to another department",
                headers={"X-Error-Code": "DEPARTMENT_MISMATCH"},
            )

        from_status = request.status
        if from_status == new_status:
            return request  # no-op, no spurious event

        now = datetime.now(timezone.utc)
        request.status = new_status
        # Picking a request up claims it for the actor if unassigned.
        if new_status == RequestStatus.in_progress and request.assigned_to is None:
            request.assigned_to = ctx.user_id
        if new_status == RequestStatus.completed:
            request.completed_at = now
            request.resolution_time_mins = max(
                0, int((now - request.created_at).total_seconds() // 60)
            )

        self.db.add(
            RequestEvent(
                request_id=request.id,
                hotel_id=request.hotel_id,
                actor_type="staff",
                actor_id=ctx.user_id,
                event_type="status_change",
                from_status=from_status,
                to_status=new_status,
                note=note,
            )
        )
        await self.db.commit()
        await self.db.refresh(request)
        return request
