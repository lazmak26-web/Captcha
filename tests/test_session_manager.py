"""
Leakers$ CAPTCHA - Session Manager Test Suite
Validates rate limiting, session expiration, attempt decrements, and anti-replay security.
"""

from __future__ import annotations

import sys
import time
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from bot.session_manager import SessionManager


class TestSessionManager(unittest.TestCase):
    """Unit tests for the verification session and anti-abuse safeguards."""

    def setUp(self) -> None:
        self.sm = SessionManager()
        self.guild_id = 11111111
        self.user_id = 99999999

    def test_session_creation_and_retrieval(self) -> None:
        """New sessions store challenge state and compute expiration."""
        sess = self.sm.create_session(
            guild_id=self.guild_id,
            user_id=self.user_id,
            code="ABC123",
            style_name="Collage",
            expiration_seconds=180,
            max_attempts=3,
        )
        self.assertEqual(sess.code, "ABC123")
        self.assertEqual(sess.attempts_left, 3)
        self.assertFalse(sess.is_expired)

        retrieved = self.sm.get_session(self.guild_id, self.user_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.code, "ABC123")

    def test_session_expiration(self) -> None:
        """Sessions past expires_at are purged automatically."""
        sess = self.sm.create_session(
            guild_id=self.guild_id,
            user_id=self.user_id,
            code="EXPIRE",
            style_name="Snow",
            expiration_seconds=0,  # Expired immediately
            max_attempts=3,
        )
        time.sleep(0.01)
        self.assertTrue(sess.is_expired)
        self.assertIsNone(self.sm.get_session(self.guild_id, self.user_id))

    def test_evaluate_correct_code_and_replay_prevention(self) -> None:
        """Correct submission succeeds and invalidates the session to prevent replay."""
        self.sm.create_session(
            guild_id=self.guild_id,
            user_id=self.user_id,
            code="WIN777",
            style_name="Cut",
            expiration_seconds=120,
            max_attempts=3,
        )

        # Case-insensitive submission
        is_correct, msg, attempts_left = self.sm.evaluate_code(
            self.guild_id, self.user_id, "  win777  "
        )
        self.assertTrue(is_correct)
        self.assertIn("successful", msg.lower())

        # Anti-replay check: session must be invalidated
        self.assertIsNone(self.sm.get_session(self.guild_id, self.user_id))

        # Re-submitting same code fails
        is_replayed, replay_msg, _ = self.sm.evaluate_code(
            self.guild_id, self.user_id, "WIN777"
        )
        self.assertFalse(is_replayed)
        self.assertIn("expired", replay_msg.lower())

    def test_failed_attempt_decrement_and_cooldown(self) -> None:
        """Incorrect submissions decrement attempts until exhausted."""
        self.sm.create_session(
            guild_id=self.guild_id,
            user_id=self.user_id,
            code="SECRET",
            style_name="Darts",
            expiration_seconds=120,
            max_attempts=2,
        )

        # Attempt 1 (wrong)
        is_correct, msg, left = self.sm.evaluate_code(self.guild_id, self.user_id, "WRONG1")
        self.assertFalse(is_correct)
        self.assertEqual(left, 1)

        # Attempt 2 (wrong, exhausts attempts)
        is_correct, msg, left = self.sm.evaluate_code(self.guild_id, self.user_id, "WRONG2")
        self.assertFalse(is_correct)
        self.assertEqual(left, 0)

        # Session should be invalidated
        self.assertIsNone(self.sm.get_session(self.guild_id, self.user_id))

    def test_incorrect_submission_dynamic_code_replacement(self) -> None:
        """Verifies session retains state and accepts updated challenge code on retry."""
        sess = self.sm.create_session(
            guild_id=self.guild_id,
            user_id=self.user_id,
            code="INITIAL1",
            style_name="MarketShapes",
            expiration_seconds=180,
            max_attempts=3,
        )

        # User submits wrong code
        is_correct, msg, left = self.sm.evaluate_code(self.guild_id, self.user_id, "INCORRECT")
        self.assertFalse(is_correct)
        self.assertEqual(left, 2)

        # Simulate automatic replacement of challenge
        sess.code = "NEWCODE2"
        sess.image_bytes = b"new_png_bytes"

        # Old code now fails
        is_old_correct, _, _ = self.sm.evaluate_code(self.guild_id, self.user_id, "INITIAL1")
        self.assertFalse(is_old_correct)
        self.assertEqual(sess.attempts_left, 1)

        # New code succeeds
        is_new_correct, _, _ = self.sm.evaluate_code(self.guild_id, self.user_id, "NEWCODE2")
        self.assertTrue(is_new_correct)

    def test_penalty_cooldown(self) -> None:
        """Penalizing cooldown blocks until duration has elapsed."""
        self.assertIsNone(self.sm.get_cooldown_remaining(self.guild_id, self.user_id))
        self.sm.trigger_cooldown(self.guild_id, self.user_id, duration_seconds=5)

        remaining = self.sm.get_cooldown_remaining(self.guild_id, self.user_id)
        self.assertIsNotNone(remaining)
        self.assertGreater(remaining, 0)

    def test_rate_limiting_anti_spam(self) -> None:
        """Rapid interactions within interval are throttled."""
        # First interaction: allowed
        throttled = self.sm.is_rate_limited(self.guild_id, self.user_id, min_interval=1.0)
        self.assertFalse(throttled)

        # Immediate follow-up: throttled
        throttled_again = self.sm.is_rate_limited(self.guild_id, self.user_id, min_interval=1.0)
        self.assertTrue(throttled_again)


def main() -> int:
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSessionManager)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())

