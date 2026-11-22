from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from sinner.cogs.profiling import humanize, profile_member, risk_level

NOW = datetime.now(timezone.utc)


def make_member(age_days, avatar=True, flags=1, name="alice", global_name="Alice", join_delay_min=600, bot=False):
    created = NOW - timedelta(days=age_days)
    return SimpleNamespace(
        created_at=created,
        joined_at=created + timedelta(minutes=join_delay_min),
        avatar="hash" if avatar else None,
        public_flags=SimpleNamespace(value=flags),
        name=name,
        global_name=global_name,
        bot=bot,
    )


def test_old_normal_account_is_safe():
    score, bad, good = profile_member(make_member(900))
    assert score < 20 and not bad and good
    assert risk_level(score)[0].startswith("🟢")


def test_fresh_spammy_account_is_very_suspicious():
    member = make_member(0.01, avatar=False, flags=0, name="free_nitro_9999", join_delay_min=1)
    score, bad, _ = profile_member(member)
    assert score >= 70 and bad
    assert risk_level(score)[0].startswith("🔴")


def test_score_is_capped_at_100():
    member = make_member(0.01, avatar=False, flags=0, name="discord.gg/x1234567", join_delay_min=1)
    assert profile_member(member, join_count=50)[0] == 100


def test_humanize():
    assert humanize(timedelta(seconds=30)) == "30 s"
    assert humanize(timedelta(minutes=5)) == "5 min"
    assert humanize(timedelta(hours=3, minutes=2)) == "3 h 2 min"
    assert humanize(timedelta(days=10)) == "10 jours"
