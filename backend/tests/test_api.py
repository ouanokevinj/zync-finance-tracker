"""
Backend edge case tests — Supabase is fully mocked, no real DB needed.
"""
import os
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test-key")

from unittest.mock import MagicMock, patch

# Patch create_client before main.py is imported so the module-level
# supabase = create_client(...) call doesn't hit the network.
_mock_supabase = MagicMock()
with patch("supabase.create_client", return_value=_mock_supabase):
    from fastapi.testclient import TestClient
    import main
    main.supabase = _mock_supabase
    from main import app

# Data endpoints depend on get_db (which verifies a JWT and builds an authed
# client). Override it to hand back the mock so tests exercise the route logic
# without real auth. Auth-specific behaviour is covered in its own tests below.
app.dependency_overrides[main.get_db] = lambda: _mock_supabase

# Rate limiting is verified manually (see plan); disable it here so repeated
# calls in the suite don't trip the limiter.
main.limiter.enabled = False

client = TestClient(app)

# ── helpers ───────────────────────────────────────────────────

SAMPLE_EARNING = {
    "id": "11111111-0000-0000-0000-000000000001",
    "amount": 1500.0,
    "source": "Freelance",
    "date": "2024-06-01",
    "created_at": "2024-06-01T10:00:00",
}

SAMPLE_SUB = {
    "id": "22222222-0000-0000-0000-000000000001",
    "name": "Netflix",
    "amount": 15.99,
    "date_started": "2024-01-01",
    "created_at": "2024-01-01T00:00:00",
}


def chain(data=None):
    """
    Build a mock Supabase query chain.
    Every chaining method returns self; .execute() returns a result with .data.
    """
    result = MagicMock()
    result.data = data if data is not None else []
    c = MagicMock()
    for method in ("select", "order", "insert", "delete", "eq", "filter", "single"):
        getattr(c, method).return_value = c
    c.execute.return_value = result
    return c


def mock_table(data=None):
    """Shortcut: patch supabase.table() to return a chain with given data."""
    _mock_supabase.table.return_value = chain(data)


def mock_table_by_name(mapping: dict):
    """
    For endpoints that call supabase.table() with different table names
    (e.g. /api/summary), return different data per table.
    """
    def side_effect(name):
        return chain(mapping.get(name, []))
    _mock_supabase.table.side_effect = side_effect


def clear_side_effect():
    _mock_supabase.table.side_effect = None


# ═══════════════════════════════════════════════════════════════
# GET /api/earnings
# ═══════════════════════════════════════════════════════════════

class TestGetEarnings:
    def test_empty_db_returns_empty_list(self):
        mock_table([])
        r = client.get("/api/earnings")
        assert r.status_code == 200
        assert r.json() == []

    def test_returns_all_rows(self):
        mock_table([SAMPLE_EARNING])
        r = client.get("/api/earnings")
        assert r.status_code == 200
        assert len(r.json()) == 1
        assert r.json()[0]["source"] == "Freelance"


# ═══════════════════════════════════════════════════════════════
# POST /api/earnings
# ═══════════════════════════════════════════════════════════════

class TestCreateEarning:
    def test_valid_payload_returns_201(self):
        mock_table([SAMPLE_EARNING])
        r = client.post("/api/earnings", json={"amount": 1500.0, "source": "Freelance", "date": "2024-06-01"})
        assert r.status_code == 201

    def test_missing_source_returns_422(self):
        r = client.post("/api/earnings", json={"amount": 100.0, "date": "2024-06-01"})
        assert r.status_code == 422

    def test_missing_amount_returns_422(self):
        r = client.post("/api/earnings", json={"source": "Work", "date": "2024-06-01"})
        assert r.status_code == 422

    def test_missing_date_returns_422(self):
        r = client.post("/api/earnings", json={"amount": 100.0, "source": "Work"})
        assert r.status_code == 422

    def test_invalid_date_format_returns_422(self):
        r = client.post("/api/earnings", json={"amount": 100.0, "source": "Work", "date": "June 2024"})
        assert r.status_code == 422

    def test_string_amount_returns_422(self):
        r = client.post("/api/earnings", json={"amount": "lots", "source": "Work", "date": "2024-06-01"})
        assert r.status_code == 422

    def test_empty_body_returns_422(self):
        r = client.post("/api/earnings", json={})
        assert r.status_code == 422

    def test_zero_amount_is_accepted(self):
        """Zero is technically valid — business logic can block it in the future."""
        row = {**SAMPLE_EARNING, "amount": 0.0}
        mock_table([row])
        r = client.post("/api/earnings", json={"amount": 0.0, "source": "Adjustment", "date": "2024-06-01"})
        assert r.status_code == 201

    def test_very_large_amount(self):
        row = {**SAMPLE_EARNING, "amount": 9_999_999.99}
        mock_table([row])
        r = client.post("/api/earnings", json={"amount": 9_999_999.99, "source": "Big win", "date": "2024-06-01"})
        assert r.status_code == 201

    def test_decimal_precision(self):
        row = {**SAMPLE_EARNING, "amount": 1234.56}
        mock_table([row])
        r = client.post("/api/earnings", json={"amount": 1234.56, "source": "Work", "date": "2024-06-01"})
        assert r.status_code == 201

    def test_future_date_is_accepted(self):
        row = {**SAMPLE_EARNING, "date": "2099-12-31"}
        mock_table([row])
        r = client.post("/api/earnings", json={"amount": 100.0, "source": "Work", "date": "2099-12-31"})
        assert r.status_code == 201

    def test_supabase_failure_returns_500(self):
        mock_table([])   # empty .data triggers the 500 guard
        r = client.post("/api/earnings", json={"amount": 100.0, "source": "Work", "date": "2024-06-01"})
        assert r.status_code == 500


# ═══════════════════════════════════════════════════════════════
# DELETE /api/earnings/{id}
# ═══════════════════════════════════════════════════════════════

class TestDeleteEarning:
    def test_delete_existing_returns_204(self):
        mock_table([SAMPLE_EARNING])
        r = client.delete(f"/api/earnings/{SAMPLE_EARNING['id']}")
        assert r.status_code == 204
        assert r.content == b""   # 204 must have no body

    def test_delete_non_existent_returns_404(self):
        mock_table([])
        r = client.delete("/api/earnings/does-not-exist")
        assert r.status_code == 404

    def test_delete_malformed_uuid_returns_404(self):
        mock_table([])
        r = client.delete("/api/earnings/not-a-uuid-at-all")
        assert r.status_code == 404


# ═══════════════════════════════════════════════════════════════
# GET /api/subscriptions
# ═══════════════════════════════════════════════════════════════

class TestGetSubscriptions:
    def test_empty_db_returns_empty_list(self):
        mock_table([])
        r = client.get("/api/subscriptions")
        assert r.status_code == 200
        assert r.json() == []

    def test_returns_all_rows(self):
        mock_table([SAMPLE_SUB])
        r = client.get("/api/subscriptions")
        assert r.status_code == 200
        assert r.json()[0]["name"] == "Netflix"


# ═══════════════════════════════════════════════════════════════
# POST /api/subscriptions
# ═══════════════════════════════════════════════════════════════

class TestCreateSubscription:
    def test_valid_payload_returns_201(self):
        mock_table([SAMPLE_SUB])
        r = client.post("/api/subscriptions", json={"name": "Netflix", "amount": 15.99, "date_started": "2024-01-01"})
        assert r.status_code == 201

    def test_missing_name_returns_422(self):
        r = client.post("/api/subscriptions", json={"amount": 15.99, "date_started": "2024-01-01"})
        assert r.status_code == 422

    def test_missing_amount_returns_422(self):
        r = client.post("/api/subscriptions", json={"name": "Netflix", "date_started": "2024-01-01"})
        assert r.status_code == 422

    def test_missing_date_started_returns_422(self):
        r = client.post("/api/subscriptions", json={"name": "Netflix", "amount": 15.99})
        assert r.status_code == 422

    def test_invalid_date_returns_422(self):
        r = client.post("/api/subscriptions", json={"name": "Netflix", "amount": 15.99, "date_started": "January 2024"})
        assert r.status_code == 422

    def test_empty_body_returns_422(self):
        r = client.post("/api/subscriptions", json={})
        assert r.status_code == 422

    def test_supabase_failure_returns_500(self):
        mock_table([])
        r = client.post("/api/subscriptions", json={"name": "Netflix", "amount": 15.99, "date_started": "2024-01-01"})
        assert r.status_code == 500


# ═══════════════════════════════════════════════════════════════
# DELETE /api/subscriptions/{id}
# ═══════════════════════════════════════════════════════════════

class TestDeleteSubscription:
    def test_delete_existing_returns_204(self):
        mock_table([SAMPLE_SUB])
        r = client.delete(f"/api/subscriptions/{SAMPLE_SUB['id']}")
        assert r.status_code == 204

    def test_delete_non_existent_returns_404(self):
        mock_table([])
        r = client.delete("/api/subscriptions/does-not-exist")
        assert r.status_code == 404


# ═══════════════════════════════════════════════════════════════
# GET /api/summary
# ═══════════════════════════════════════════════════════════════

class TestSummary:
    def setup_method(self):
        clear_side_effect()

    def test_empty_db_returns_zeros(self):
        mock_table_by_name({"earnings": [], "subscriptions": []})
        r = client.get("/api/summary")
        assert r.status_code == 200
        body = r.json()
        assert body["total_earnings"] == 0
        assert body["total_subscriptions"] == 0
        assert body["net"] == 0

    def test_correct_totals(self):
        mock_table_by_name({
            "earnings":      [{"amount": 5000.0}, {"amount": 3000.0}],
            "subscriptions": [{"amount": 100.0},  {"amount": 50.0}],
        })
        r = client.get("/api/summary")
        body = r.json()
        assert body["total_earnings"]      == 8000.0
        assert body["total_subscriptions"] == 150.0
        assert body["net"]                 == 7850.0

    def test_negative_net(self):
        mock_table_by_name({
            "earnings":      [{"amount": 100.0}],
            "subscriptions": [{"amount": 999.0}],
        })
        r = client.get("/api/summary")
        assert r.json()["net"] == -899.0

    def test_only_earnings_no_subs(self):
        mock_table_by_name({
            "earnings":      [{"amount": 2500.0}],
            "subscriptions": [],
        })
        r = client.get("/api/summary")
        body = r.json()
        assert body["total_earnings"]      == 2500.0
        assert body["total_subscriptions"] == 0
        assert body["net"]                 == 2500.0

    def test_only_subs_no_earnings(self):
        mock_table_by_name({
            "earnings":      [],
            "subscriptions": [{"amount": 300.0}],
        })
        r = client.get("/api/summary")
        body = r.json()
        assert body["total_earnings"]      == 0
        assert body["total_subscriptions"] == 300.0
        assert body["net"]                 == -300.0

    def test_decimal_precision_in_net(self):
        mock_table_by_name({
            "earnings":      [{"amount": 100.01}],
            "subscriptions": [{"amount": 0.01}],
        })
        r = client.get("/api/summary")
        assert round(r.json()["net"], 2) == 100.0


# ═══════════════════════════════════════════════════════════════
# Auth — data endpoints require a valid token
# ═══════════════════════════════════════════════════════════════

class TestAuthRequired:
    def test_missing_token_returns_401(self):
        """Without the get_db override, a request with no bearer token is rejected."""
        app.dependency_overrides.pop(main.get_db, None)
        try:
            r = client.get("/api/earnings")
            assert r.status_code == 401
        finally:
            app.dependency_overrides[main.get_db] = lambda: _mock_supabase


# ═══════════════════════════════════════════════════════════════
# POST /api/auth/register — input validation
# ═══════════════════════════════════════════════════════════════

class TestRegisterValidation:
    def test_missing_email_returns_422(self):
        r = client.post("/api/auth/register", json={"username": "kevin", "password": "supersecret"})
        assert r.status_code == 422

    def test_invalid_email_returns_422(self):
        r = client.post("/api/auth/register", json={"email": "not-an-email", "username": "kevin", "password": "supersecret"})
        assert r.status_code == 422

    def test_short_password_returns_422(self):
        r = client.post("/api/auth/register", json={"email": "a@b.com", "username": "kevin", "password": "short"})
        assert r.status_code == 422

    def test_bad_username_chars_returns_422(self):
        r = client.post("/api/auth/register", json={"email": "a@b.com", "username": "has spaces!", "password": "supersecret"})
        assert r.status_code == 422


# ═══════════════════════════════════════════════════════════════
# POST /api/auth/login
# ═══════════════════════════════════════════════════════════════

class TestLogin:
    def teardown_method(self):
        main.supabase.auth.sign_in_with_password.side_effect = None

    def test_valid_credentials_return_tokens(self):
        session = MagicMock(access_token="access-123", refresh_token="refresh-456")
        user    = MagicMock(id="uid-1", email="a@b.com", user_metadata={"username": "kevin"})
        main.supabase.auth.sign_in_with_password.return_value = MagicMock(session=session, user=user)

        r = client.post("/api/auth/login", json={"email": "a@b.com", "password": "supersecret"})
        assert r.status_code == 200
        body = r.json()
        assert body["access_token"] == "access-123"
        assert body["refresh_token"] == "refresh-456"
        assert body["user"]["username"] == "kevin"

    def test_bad_credentials_return_401(self):
        main.supabase.auth.sign_in_with_password.side_effect = Exception("invalid")
        r = client.post("/api/auth/login", json={"email": "a@b.com", "password": "wrongpass"})
        assert r.status_code == 401

    def test_missing_password_returns_422(self):
        r = client.post("/api/auth/login", json={"email": "a@b.com"})
        assert r.status_code == 422
