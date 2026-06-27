import os

import httpx
from dotenv import load_dotenv
from strands import tool

load_dotenv()

BASE_URL = "https://api.cal.com/v2"


def _api_key():
    key = os.environ.get("CAL_API_KEY")
    if not key:
        raise ValueError("CAL_API_KEY environment variable is not set")
    return key


_DEFAULT_TIMEOUT = 60  # seconds


def _client(api_version: str | None = None, timeout: int = _DEFAULT_TIMEOUT):
    headers = {
        "Authorization": f"Bearer {_api_key()}",
        "Content-Type": "application/json",
    }
    if api_version:
        headers["cal-api-version"] = api_version
    return httpx.AsyncClient(base_url=BASE_URL, headers=headers, timeout=timeout)


def _check(r: httpx.Response) -> dict:
    try:
        r.raise_for_status()
    except httpx.HTTPStatusError as e:
        body = e.response.text
        raise RuntimeError(f"Cal.com API error {e.response.status_code}: {body}") from e
    return r.json()


def make_cal_tools():
    _api_key()  # eager validation; raises ValueError if key is missing

    @tool
    async def get_me() -> dict:
        """Get the current user's Cal.com profile.

        Returns user information: id, username, email, name, timeZone,
        defaultScheduleId, weekStart, etc.
        """
        async with _client() as c:
            r = await c.get("/me")
            return _check(r)

    @tool
    async def get_event_types(
        username: str | None = None,
        event_slug: str | None = None,
    ) -> dict:
        """List event types for the authenticated user or a specified user.

        Args:
            username: Optional Cal.com username to fetch event types for.
            event_slug: Optional slug filter (requires username).

        Returns:
            List of event types with id, lengthInMinutes, title, slug, etc.
        """
        params = {}
        if username:
            params["username"] = username
        if event_slug:
            params["eventSlug"] = event_slug
        async with _client(api_version="2024-06-14") as c:
            r = await c.get("/event-types", params=params)
            return _check(r)

    @tool
    async def get_event_type(event_type_id: int) -> dict:
        """Get details of a specific event type.

        Args:
            event_type_id: Numeric ID of the event type.

        Returns:
            Event type details including length, title, slug, locations, etc.
        """
        async with _client(api_version="2024-06-14") as c:
            r = await c.get(f"/event-types/{event_type_id}")
            return _check(r)

    @tool
    async def create_event_type(
        length_in_minutes: int,
        title: str,
        slug: str,
        description: str = "",
        locations: list[dict] | None = None,
        disable_guests: bool = False,
        slot_interval: int | None = None,
        minimum_booking_notice: int | None = None,
        before_event_buffer: int | None = None,
        after_event_buffer: int | None = None,
        schedule_id: int | None = None,
        seats: dict | None = None,
        recurrence: dict | None = None,
        requires_booker_email_verification: bool = False,
        hide_calendar_notes: bool = False,
        metadata: dict | None = None,
        data: dict | None = None,
    ) -> dict:
        """Create a new event type.

        Args:
            length_in_minutes: Duration of the event in minutes.
            title: Display title for the event type.
            slug: URL-friendly identifier (e.g. "30-min-meeting").
            description: Optional description.
            locations: List of location objects, e.g. [{"type": "integrations:daily"}].
            disable_guests: Whether to disable guest invitations (default False).
            slot_interval: Minutes between available slots.
            minimum_booking_notice: Minimum hours of notice before booking.
            before_event_buffer: Buffer minutes before event.
            after_event_buffer: Buffer minutes after event.
            schedule_id: Schedule ID to use for availability.
            seats: Seats config, e.g. {"seatsPerTimeSlot": 5}.
            recurrence: Recurrence config, e.g. {"frequency": "weekly", "interval": 1}.
            requires_booker_email_verification: Require email verification to book.
            hide_calendar_notes: Hide calendar notes from attendees.
            metadata: Custom metadata dict.
            data: Additional fields to include in the request body.

        Returns:
            Created event type details.
        """
        body = {
            "lengthInMinutes": length_in_minutes,
            "title": title,
            "slug": slug,
        }
        if description:
            body["description"] = description
        if locations:
            body["locations"] = locations
        if disable_guests:
            body["disableGuests"] = True
        if slot_interval is not None:
            body["slotInterval"] = slot_interval
        if minimum_booking_notice is not None:
            body["minimumBookingNotice"] = minimum_booking_notice
        if before_event_buffer is not None:
            body["beforeEventBuffer"] = before_event_buffer
        if after_event_buffer is not None:
            body["afterEventBuffer"] = after_event_buffer
        if schedule_id is not None:
            body["scheduleId"] = schedule_id
        if seats:
            body["seats"] = seats
        if recurrence:
            body["recurrence"] = recurrence
        if requires_booker_email_verification:
            body["requiresBookerEmailVerification"] = True
        if hide_calendar_notes:
            body["hideCalendarNotes"] = True
        if metadata:
            body["metadata"] = metadata
        if data:
            body.update(data)
        async with _client(api_version="2024-06-14") as c:
            r = await c.post("/event-types", json=body)
            return _check(r)

    @tool
    async def update_event_type(
        event_type_id: int,
        length_in_minutes: int | None = None,
        title: str | None = None,
        slug: str | None = None,
        description: str | None = None,
        locations: list[dict] | None = None,
        disable_guests: bool | None = None,
        slot_interval: int | None = None,
        minimum_booking_notice: int | None = None,
        before_event_buffer: int | None = None,
        after_event_buffer: int | None = None,
        schedule_id: int | None = None,
        seats: dict | None = None,
        recurrence: dict | None = None,
        requires_booker_email_verification: bool | None = None,
        hide_calendar_notes: bool | None = None,
        metadata: dict | None = None,
        data: dict | None = None,
    ) -> dict:
        """Update an existing event type. Only provided fields are changed.

        Args:
            event_type_id: Numeric ID of the event type to update.
            length_in_minutes: New duration in minutes.
            title: New display title.
            slug: New URL-friendly slug.
            description: New description.
            locations: New list of location objects.
            disable_guests: Whether to disable guest invitations.
            slot_interval: New slot interval in minutes.
            minimum_booking_notice: New minimum notice in hours.
            before_event_buffer: New pre-event buffer in minutes.
            after_event_buffer: New post-event buffer in minutes.
            schedule_id: New schedule ID.
            seats: New seats configuration.
            recurrence: New recurrence configuration.
            requires_booker_email_verification: Require email verification.
            hide_calendar_notes: Hide calendar notes.
            metadata: New custom metadata.
            data: Additional optional fields.

        Returns:
            Updated event type details.
        """
        body: dict = {}
        if length_in_minutes is not None:
            body["lengthInMinutes"] = length_in_minutes
        if title is not None:
            body["title"] = title
        if slug is not None:
            body["slug"] = slug
        if description is not None:
            body["description"] = description
        if locations is not None:
            body["locations"] = locations
        if disable_guests is not None:
            body["disableGuests"] = disable_guests
        if slot_interval is not None:
            body["slotInterval"] = slot_interval
        if minimum_booking_notice is not None:
            body["minimumBookingNotice"] = minimum_booking_notice
        if before_event_buffer is not None:
            body["beforeEventBuffer"] = before_event_buffer
        if after_event_buffer is not None:
            body["afterEventBuffer"] = after_event_buffer
        if schedule_id is not None:
            body["scheduleId"] = schedule_id
        if seats is not None:
            body["seats"] = seats
        if recurrence is not None:
            body["recurrence"] = recurrence
        if requires_booker_email_verification is not None:
            body["requiresBookerEmailVerification"] = requires_booker_email_verification
        if hide_calendar_notes is not None:
            body["hideCalendarNotes"] = hide_calendar_notes
        if metadata is not None:
            body["metadata"] = metadata
        if data:
            body.update(data)
        async with _client(api_version="2024-06-14") as c:
            r = await c.patch(f"/event-types/{event_type_id}", json=body)
            return _check(r)

    @tool
    async def delete_event_type(event_type_id: int) -> dict:
        """Delete an event type.

        Args:
            event_type_id: Numeric ID of the event type to delete.

        Returns:
            Confirmation with deleted event type details.
        """
        async with _client(api_version="2024-06-14") as c:
            r = await c.delete(f"/event-types/{event_type_id}")
            return _check(r)

    @tool
    async def get_bookings(
        status: str | None = None,
        attendee_email: str | None = None,
        after_start: str | None = None,
        before_end: str | None = None,
        limit: int = 50,
        cursor: str | None = None,
    ) -> dict:
        """List bookings with optional filters.

        Args:
            status: Filter by status (upcoming, recurring, past, cancelled, unconfirmed).
            attendee_email: Filter by attendee email.
            after_start: ISO date string to filter bookings starting after.
            before_end: ISO date string to filter bookings ending before.
            limit: Max results per page (default 50).
            cursor: Pagination cursor from a previous response.

        Returns:
            List of bookings with pagination info.
        """
        params = {"limit": str(limit)}
        if status:
            params["status"] = status
        if attendee_email:
            params["attendeeEmail"] = attendee_email
        if after_start:
            params["afterStart"] = after_start
        if before_end:
            params["beforeEnd"] = before_end
        if cursor:
            params["cursor"] = cursor
        async with _client(api_version="2026-05-01") as c:
            r = await c.get("/bookings", params=params)
            return _check(r)

    @tool
    async def get_booking(booking_uid: str) -> dict:
        """Get details of a specific booking.

        Args:
            booking_uid: The UID of the booking.

        Returns:
            Booking details including status, start, end, attendees, etc.
        """
        async with _client(api_version="2026-02-25") as c:
            r = await c.get(f"/bookings/{booking_uid}")
            return _check(r)

    @tool
    async def create_booking(
        start: str,
        event_type_id: int,
        attendee_name: str,
        attendee_email: str = "",
        attendee_time_zone: str = "Asia/Kolkata",
        attendee_language: str = "en",
        guests: list[str] | None = None,
        meeting_url: str | None = None,
        metadata: dict | None = None,
    ) -> dict:
        """Create a new booking.

        Args:
            start: ISO 8601 UTC start time (e.g. "2026-06-25T10:00:00.000Z").
            event_type_id: Numeric ID of the event type to book.
            attendee_name: Name of the primary attendee.
            attendee_email: Email of the attendee.
            attendee_time_zone: IANA timezone string (default Asia/Kolkata).
            attendee_language: Language code (default "en").
            guests: Optional list of guest email addresses.
            meeting_url: Location URL for the meeting (e.g. Google Meet link).
            metadata: Optional dict of custom metadata.

        Returns:
            Created booking details.
        """
        body = {
            "start": start,
            "eventTypeId": event_type_id,
            "attendee": {
                "name": attendee_name,
                "email": attendee_email,
                "timeZone": attendee_time_zone,
                "language": attendee_language,
            },
        }
        if guests:
            body["guests"] = guests
        if meeting_url:
            body["location"] = {"type": "link", "url": meeting_url}
        if metadata:
            body["metadata"] = metadata
        async with _client(api_version="2026-02-25") as c:
            r = await c.post("/bookings", json=body)
            return _check(r)

    @tool
    async def cancel_booking(
        booking_uid: str,
        cancellation_reason: str = "",
    ) -> dict:
        """Cancel a booking.

        Args:
            booking_uid: The UID of the booking to cancel.
            cancellation_reason: Optional reason for cancellation.

        Returns:
            Cancelled booking details.
        """
        body = {"cancellationReason": cancellation_reason or "Cancelled by user request"}
        async with _client(api_version="2026-02-25") as c:
            r = await c.post(f"/bookings/{booking_uid}/cancel", json=body)
            return _check(r)

    @tool
    async def reschedule_booking(
        booking_uid: str,
        start: str,
        reschedule_reason: str = "",
    ) -> dict:
        """Reschedule a booking to a new time.

        Args:
            booking_uid: The UID of the booking to reschedule.
            start: New ISO 8601 UTC start time.
            reschedule_reason: Optional reason for rescheduling.

        Returns:
            New booking details at the rescheduled time.
        """
        body = {"start": start}
        if reschedule_reason:
            body["reschedulingReason"] = reschedule_reason
        async with _client(api_version="2026-02-25") as c:
            r = await c.post(f"/bookings/{booking_uid}/reschedule", json=body)
            return _check(r)

    @tool
    async def confirm_booking(booking_uid: str) -> dict:
        """Confirm a pending booking (must be the booking owner).

        Args:
            booking_uid: The UID of the booking to confirm.

        Returns:
            Confirmed booking details.
        """
        async with _client(api_version="2026-02-25") as c:
            r = await c.post(f"/bookings/{booking_uid}/confirm")
            return _check(r)

    @tool
    async def mark_booking_absent(
        booking_uid: str,
        host: bool = False,
        attendee_emails: list[str] | None = None,
    ) -> dict:
        """Mark a booking host or attendees as absent.

        Args:
            booking_uid: The UID of the booking.
            host: Mark the host as absent (default False).
            attendee_emails: List of attendee emails to mark absent.

        Returns:
            Updated booking details.
        """
        body = {}
        if host:
            body["host"] = True
        if attendee_emails:
            body["attendees"] = [
                {"email": email, "absent": True}
                for email in attendee_emails
            ]
        async with _client(api_version="2026-02-25") as c:
            r = await c.post(f"/bookings/{booking_uid}/mark-absent", json=body)
            return _check(r)

    @tool
    async def get_schedules() -> dict:
        """List all schedules for the authenticated user.

        Returns:
            List of schedules with id, name, timeZone, availability, etc.
        """
        async with _client(api_version="2024-06-11") as c:
            r = await c.get("/schedules")
            return _check(r)

    @tool
    async def get_schedule(schedule_id: int) -> dict:
        """Get details of a specific schedule.

        Args:
            schedule_id: Numeric ID of the schedule.

        Returns:
            Schedule details with availability and overrides.
        """
        async with _client(api_version="2024-06-11") as c:
            r = await c.get(f"/schedules/{schedule_id}")
            return _check(r)

    @tool
    async def get_default_schedule() -> dict:
        """Get the default schedule for the authenticated user.

        Returns:
            Default schedule with id, name, timeZone, availability, etc.
        """
        async with _client(api_version="2024-06-11") as c:
            r = await c.get("/schedules/default")
            return _check(r)

    @tool
    async def create_schedule(
        name: str,
        time_zone: str,
        is_default: bool = False,
        availability: list[dict] | None = None,
        overrides: list[dict] | None = None,
    ) -> dict:
        """Create a new schedule.

        Args:
            name: Display name for the schedule.
            time_zone: IANA timezone (e.g. "Asia/Kolkata").
            is_default: Whether this should be the default schedule.
            availability: List of availability blocks, each with
                days (list of weekday names), startTime (HH:MM), endTime (HH:MM).
                Example: [{"days": ["Monday","Tuesday"], "startTime": "09:00", "endTime": "17:00"}]
            overrides: List of date overrides, each with date (YYYY-MM-DD),
                startTime, endTime.

        Returns:
            Created schedule details.
        """
        body = {
            "name": name,
            "timeZone": time_zone,
            "isDefault": is_default,
        }
        if availability:
            body["availability"] = availability
        if overrides:
            body["overrides"] = overrides
        async with _client(api_version="2024-06-11") as c:
            r = await c.post("/schedules", json=body)
            return _check(r)

    @tool
    async def update_schedule(
        schedule_id: int,
        name: str | None = None,
        time_zone: str | None = None,
        is_default: bool | None = None,
        availability: list[dict] | None = None,
        overrides: list[dict] | None = None,
    ) -> dict:
        """Update an existing schedule.

        Args:
            schedule_id: Numeric ID of the schedule to update.
            name: New display name.
            time_zone: New IANA timezone.
            is_default: Set as default schedule.
            availability: New availability blocks (replaces existing).
            overrides: New date overrides (replaces existing).

        Returns:
            Updated schedule details.
        """
        body: dict = {}
        if name is not None:
            body["name"] = name
        if time_zone is not None:
            body["timeZone"] = time_zone
        if is_default is not None:
            body["isDefault"] = is_default
        if availability is not None:
            body["availability"] = availability
        if overrides is not None:
            body["overrides"] = overrides
        async with _client(api_version="2024-06-11") as c:
            r = await c.patch(f"/schedules/{schedule_id}", json=body)
            return _check(r)

    @tool
    async def delete_schedule(schedule_id: int) -> dict:
        """Delete a schedule.

        Args:
            schedule_id: Numeric ID of the schedule to delete.

        Returns:
            Confirmation status.
        """
        async with _client(api_version="2024-06-11") as c:
            r = await c.delete(f"/schedules/{schedule_id}")
            return _check(r)

    @tool
    async def get_availability(
        start: str,
        end: str,
        event_type_id: int | None = None,
        event_type_slug: str | None = None,
        username: str | None = None,
        time_zone: str | None = None,
        duration: int | None = None,
    ) -> dict:
        """Get available time slots for booking.

        Provide either event_type_id (recommended) or event_type_slug + username.

        Args:
            start: ISO date/dateTime for the start of the range.
            end: ISO date/dateTime for the end of the range.
            event_type_id: Numeric ID of the event type.
            event_type_slug: Slug of the event type (requires username).
            username: Cal.com username (required if using event_type_slug).
            time_zone: IANA timezone for slot display.
            duration: Slot duration in minutes (overrides event type default).

        Returns:
            Dictionary mapping dates to available time slots.
        """
        params = {"start": start, "end": end}
        if event_type_id:
            params["eventTypeId"] = str(event_type_id)
        if event_type_slug:
            params["eventTypeSlug"] = event_type_slug
        if username:
            params["username"] = username
        if time_zone:
            params["timeZone"] = time_zone
        if duration:
            params["duration"] = str(duration)
        async with _client(api_version="2024-09-04") as c:
            r = await c.get("/slots", params=params)
            return _check(r)

    @tool
    async def get_busy_times(
        date_from: str,
        date_to: str,
        calendars_to_load: str,
        time_zone: str = "Asia/Kolkata",
    ) -> dict:
        """Get busy times from connected calendars.

        Args:
            date_from: Start date (YYYY-MM-DD).
            date_to: End date (YYYY-MM-DD).
            calendars_to_load: JSON array of calendar credentials.
                Find credential IDs via your Cal.com dashboard under
                "Apps & Integrations" → connected calendars.
                Example: '[{"credentialId": 123, "externalId": "abc@group.calendar.google.com"}]'
            time_zone: IANA timezone (default Asia/Kolkata).

        Returns:
            List of busy time blocks with start, end, and source.
        """
        import json as _json
        items = _json.loads(calendars_to_load)
        params: list[tuple[str, str]] = [
            ("dateFrom", date_from),
            ("dateTo", date_to),
            ("timeZone", time_zone),
        ]
        for i, item in enumerate(items):
            cred = item.get("credentialId")
            if cred is None:
                cred = item.get("credential_id")
            ext = item.get("externalId")
            if ext is None:
                ext = item.get("external_id")
            params.append(
                (f"calendarsToLoad[{i}][credentialId]", str(cred) if cred is not None else "")
            )
            params.append(
                (f"calendarsToLoad[{i}][externalId]", str(ext or ""))
            )
        async with _client() as c:
            r = await c.get("/calendars/busy-times", params=params)
            return _check(r)

    return [
        get_me,
        get_event_types,
        get_event_type,
        create_event_type,
        update_event_type,
        delete_event_type,
        get_bookings,
        get_booking,
        create_booking,
        cancel_booking,
        reschedule_booking,
        confirm_booking,
        mark_booking_absent,
        get_schedules,
        get_schedule,
        get_default_schedule,
        create_schedule,
        update_schedule,
        delete_schedule,
        get_availability,
        get_busy_times,
    ]
