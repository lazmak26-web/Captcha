"""
Leakers$ CAPTCHA - Session & Security Manager
Tracks verification challenges, active sessions, replay prevention, and rate-limiting.
"""

from __future__ import annotations

import time
import logging
from dataclasses import dataclass
from typing import Optional, Tuple

logger = logging.getLogger("leakers_captcha.session")


@dataclass
class VerificationSession:
    """Represents an active in-flight CAPTCHA session for a specific guild member."""
    guild_id: int
    user_id: int
    code: str
    style_name: str
    created_at: float
    expires_at: float
    max_attempts: int
    attempts_left: int
    image_bytes: Optional[bytes] = None
    is_solved: bool = False

    @property
    def is_expired(self) -> bool:
        """Determines if the session has passed its expiration epoch."""
        return time.time() > self.expires_at

    @property
    def seconds_remaining(self) -> int:
        """Returns the remaining valid seconds for the active session."""
        return max(0, int(self.expires_at - time.time()))


class SessionManager:
    """
    Thread-safe in-memory session manager with active challenge isolation,
    anti-replay defense, and rate-limiting.
    """

    def __init__(self) -> None:
        # Key: (guild_id, user_id) -> VerificationSession
        self._sessions: dict[Tuple[int, int], VerificationSession] = {}
        # Key: (guild_id, user_id) -> timestamp when cooldown lifts
        self._cooldowns: dict[Tuple[int, int], float] = {}
        # Key: (guild_id, user_id) -> timestamp of last interaction (anti-spam)
        self._last_interactions: dict[Tuple[int, int], float] = {}

    def is_rate_limited(self, guild_id: int, user_id: int, min_interval: float = 2.0) -> bool:
        """
        Anti-spam guard: prevents users from hammering verify buttons or modals.
        Returns True if the interaction is throttled.
        """
        now = time.time()
        key = (guild_id, user_id)
        last_time = self._last_interactions.get(key, 0.0)
        if now - last_time < min_interval:
            return True
        self._last_interactions[key] = now
        return False

    def get_cooldown_remaining(self, guild_id: int, user_id: int) -> Optional[int]:
        """Returns remaining cooldown seconds if member is penalized, else None."""
        key = (guild_id, user_id)
        cooldown_until = self._cooldowns.get(key)
        if cooldown_until is None:
            return None

        now = time.time()
        if now >= cooldown_until:
            del self._cooldowns[key]
            return None
        return int(cooldown_until - now)

    def trigger_cooldown(self, guild_id: int, user_id: int, duration_seconds: int) -> None:
        """Applies a penalizing cooldown after exhausting attempts."""
        key = (guild_id, user_id)
        self._cooldowns[key] = time.time() + duration_seconds
        self.invalidate_session(guild_id, user_id)
        logger.info("User %s penalized in guild %s for %ds.", user_id, guild_id, duration_seconds)

    def create_session(
        self,
        guild_id: int,
        user_id: int,
        code: str,
        style_name: str,
        expiration_seconds: int,
        max_attempts: int,
        image_bytes: Optional[bytes] = None,
    ) -> VerificationSession:
        """Constructs and stores a new isolated verification session."""
        now = time.time()
        session = VerificationSession(
            guild_id=guild_id,
            user_id=user_id,
            code=code,
            style_name=style_name,
            created_at=now,
            expires_at=now + expiration_seconds,
            max_attempts=max_attempts,
            attempts_left=max_attempts,
            image_bytes=image_bytes,
        )
        self._sessions[(guild_id, user_id)] = session
        return session

    def get_session(self, guild_id: int, user_id: int) -> Optional[VerificationSession]:
        """
        Retrieves the user's active session.
        Automatically discards and purges expired sessions.
        """
        key = (guild_id, user_id)
        session = self._sessions.get(key)
        if session is None:
            return None

        if session.is_expired or session.is_solved:
            del self._sessions[key]
            return None

        return session

    def invalidate_session(self, guild_id: int, user_id: int) -> None:
        """Purges active challenge to prevent token reuse or replay attacks."""
        key = (guild_id, user_id)
        self._sessions.pop(key, None)

    def evaluate_code(
        self,
        guild_id: int,
        user_id: int,
        submission: str,
    ) -> Tuple[bool, str, int]:
        """
        Evaluates a user-submitted code against the active session.
        Returns:
            (is_correct: bool, status_message: str, attempts_left: int)
        """
        session = self.get_session(guild_id, user_id)
        if session is None:
            return False, "Your verification session has expired. Please request a new CAPTCHA.", 0

        # Normalize comparison (case-insensitive, strip whitespace)
        cleaned_submission = submission.strip().upper()
        expected_code = session.code.strip().upper()

        if cleaned_submission == expected_code:
            session.is_solved = True
            self.invalidate_session(guild_id, user_id)
            return True, "Verification successful! Welcome to the server.", session.attempts_left

        # Failed attempt decrement
        session.attempts_left -= 1
        remaining = session.attempts_left

        if remaining <= 0:
            self.invalidate_session(guild_id, user_id)
            return False, "You have exceeded maximum allowed attempts.", 0

        return False, f"Incorrect code. You have {remaining} attempt(s) remaining.", remaining

