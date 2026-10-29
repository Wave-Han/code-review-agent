"""
Unit tests for context-aware exemptions in Detector (Day 9 improvement).

Each exemption kills one known FP from the v2 suite (T01/T02/T03)
without silencing the corresponding true positives (J-series cases).
Pairing every exemption test with a regression pin guards the
precision/recall trade-off: an exemption that is too broad would
pass its own test but fail its paired pin.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "eval"))

from eval_harness import Detector


def detected_categories(code):
    """Run the offline Detector and return category names only."""
    return [category for category, _ in Detector().detect(code)]


# --- exemption 1: test fixture class suppresses secret findings (T01) ---

def test_secret_in_test_fixture_class_is_exempted():
    # Arrange
    code = (
        "class PaymentClientTest {\n"
        "    private static final String TEST_API_KEY = \"test-key-not-real\";\n"
        "}\n"
    )
    # Act
    found = detected_categories(code)
    # Assert
    assert "hardcoded_secret" not in found


def test_secret_in_production_class_is_still_reported():
    # Arrange
    code = (
        "public class DbConfig {\n"
        "    static final String PASSWORD = \"admin123\";\n"
        "}\n"
    )
    # Act
    found = detected_categories(code)
    # Assert
    assert "hardcoded_secret" in found


# --- exemption 2: println inside main is program output, not debug (T02) ---

def test_println_in_main_is_exempted():
    # Arrange
    code = (
        "public class CliMain {\n"
        "    public static void main(String[] args) {\n"
        "        System.out.println(\"Result: \" + r.summary());\n"
        "    }\n"
        "}\n"
    )
    # Act
    found = detected_categories(code)
    # Assert
    assert "debug_print" not in found


def test_println_in_business_logic_is_still_reported():
    # Arrange
    code = (
        "public Order checkout(Cart cart) {\n"
        "    System.out.println(\"debug: cart=\" + cart);\n"
        "    return order;\n"
        "}\n"
    )
    # Act
    found = detected_categories(code)
    # Assert
    assert "debug_print" in found


# --- exemption 3: SQL in a returned string literal is documentation (T03) ---

def test_sql_in_returned_string_literal_is_exempted():
    # Arrange
    code = (
        "public String warning() {\n"
        "    return \"Never do: SELECT * FROM users WHERE name='\" + user + \"'\";\n"
        "}\n"
    )
    # Act
    found = detected_categories(code)
    # Assert
    assert "sql_injection" not in found


def test_sql_assigned_to_variable_is_still_reported():
    # Arrange
    code = (
        "public User findUser(String name) {\n"
        "    String sql = \"SELECT * FROM users WHERE name='\" + name + \"'\";\n"
        "    return jdbc.queryForObject(sql, userRowMapper);\n"
        "}\n"
    )
    # Act
    found = detected_categories(code)
    # Assert
    assert "sql_injection" in found
