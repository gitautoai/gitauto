from typing import cast

from constants.models import (
    ClaudeModelId,
    DEFAULT_FREE_MODEL,
    DEFAULT_PAID_MODEL,
    FREE_TIER_MODELS,
    GoogleModelId,
    USER_SELECTABLE_MODELS,
)
from schemas.supabase.types import Repositories
from services.webhook.utils.get_preferred_model import get_preferred_model


# --- No repo_settings (None) ---


def test_no_settings_free_user():
    result = get_preferred_model(repo_settings=None, is_paid=False)
    assert result == DEFAULT_FREE_MODEL


def test_no_settings_paid_user():
    result = get_preferred_model(repo_settings=None, is_paid=True)
    assert result == DEFAULT_PAID_MODEL


# --- repo_settings with no preferred_model ---


def test_empty_settings_free_user():
    settings = cast(Repositories, {})
    result = get_preferred_model(repo_settings=settings, is_paid=False)
    assert result == DEFAULT_FREE_MODEL


def test_empty_settings_paid_user():
    settings = cast(Repositories, {})
    result = get_preferred_model(repo_settings=settings, is_paid=True)
    assert result == DEFAULT_PAID_MODEL


def test_preferred_model_none_free_user():
    settings = cast(Repositories, {"preferred_model": None})
    result = get_preferred_model(repo_settings=settings, is_paid=False)
    assert result == DEFAULT_FREE_MODEL


def test_preferred_model_none_paid_user():
    settings = cast(Repositories, {"preferred_model": None})
    result = get_preferred_model(repo_settings=settings, is_paid=True)
    assert result == DEFAULT_PAID_MODEL


def test_preferred_model_empty_string_free_user():
    settings = cast(Repositories, {"preferred_model": ""})
    result = get_preferred_model(repo_settings=settings, is_paid=False)
    assert result == DEFAULT_FREE_MODEL


def test_preferred_model_empty_string_paid_user():
    settings = cast(Repositories, {"preferred_model": ""})
    result = get_preferred_model(repo_settings=settings, is_paid=True)
    assert result == DEFAULT_PAID_MODEL


# --- Unknown / invalid model strings ---


def test_unknown_model_free_user():
    settings = cast(Repositories, {"preferred_model": "nonexistent-model"})
    result = get_preferred_model(repo_settings=settings, is_paid=False)
    assert result == DEFAULT_FREE_MODEL


def test_unknown_model_paid_user():
    settings = cast(Repositories, {"preferred_model": "nonexistent-model"})
    result = get_preferred_model(repo_settings=settings, is_paid=True)
    assert result == DEFAULT_PAID_MODEL


def test_typo_model_free_user():
    settings = cast(Repositories, {"preferred_model": "claude-opus-4.6"})
    result = get_preferred_model(repo_settings=settings, is_paid=False)
    assert result == DEFAULT_FREE_MODEL


def test_typo_model_paid_user():
    settings = cast(Repositories, {"preferred_model": "claude-opus-4.6"})
    result = get_preferred_model(repo_settings=settings, is_paid=True)
    assert result == DEFAULT_PAID_MODEL


# --- Non-user-selectable models (fallback-only) ---


def test_non_selectable_opus_4_6_free_user():
    settings = cast(Repositories, {"preferred_model": ClaudeModelId.OPUS_4_6})
    result = get_preferred_model(repo_settings=settings, is_paid=False)
    assert result == DEFAULT_FREE_MODEL


def test_non_selectable_opus_4_6_paid_user():
    settings = cast(Repositories, {"preferred_model": ClaudeModelId.OPUS_4_6})
    result = get_preferred_model(repo_settings=settings, is_paid=True)
    assert result == DEFAULT_PAID_MODEL


def test_non_selectable_opus_4_5_free_user():
    settings = cast(Repositories, {"preferred_model": ClaudeModelId.OPUS_4_5})
    result = get_preferred_model(repo_settings=settings, is_paid=False)
    assert result == DEFAULT_FREE_MODEL


def test_non_selectable_opus_4_5_paid_user():
    settings = cast(Repositories, {"preferred_model": ClaudeModelId.OPUS_4_5})
    result = get_preferred_model(repo_settings=settings, is_paid=True)
    assert result == DEFAULT_PAID_MODEL


def test_non_selectable_sonnet_4_5_free_user():
    settings = cast(Repositories, {"preferred_model": ClaudeModelId.SONNET_4_5})
    result = get_preferred_model(repo_settings=settings, is_paid=False)
    assert result == DEFAULT_FREE_MODEL


def test_non_selectable_sonnet_4_5_paid_user():
    settings = cast(Repositories, {"preferred_model": ClaudeModelId.SONNET_4_5})
    result = get_preferred_model(repo_settings=settings, is_paid=True)
    assert result == DEFAULT_PAID_MODEL


def test_non_selectable_haiku_4_5_free_user():
    settings = cast(Repositories, {"preferred_model": ClaudeModelId.HAIKU_4_5})
    result = get_preferred_model(repo_settings=settings, is_paid=False)
    assert result == DEFAULT_FREE_MODEL


def test_non_selectable_haiku_4_5_paid_user():
    settings = cast(Repositories, {"preferred_model": ClaudeModelId.HAIKU_4_5})
    result = get_preferred_model(repo_settings=settings, is_paid=True)
    assert result == DEFAULT_PAID_MODEL


# --- Free user with valid free-tier models ---


def test_free_user_selects_gemini_2_5_flash():
    settings = cast(Repositories, {"preferred_model": GoogleModelId.GEMINI_2_5_FLASH})
    result = get_preferred_model(repo_settings=settings, is_paid=False)
    assert result == GoogleModelId.GEMINI_2_5_FLASH


def test_free_user_selects_gemma_4_31b():
    settings = cast(Repositories, {"preferred_model": GoogleModelId.GEMMA_4_31B})
    result = get_preferred_model(repo_settings=settings, is_paid=False)
    assert result == GoogleModelId.GEMMA_4_31B


def test_free_user_selects_sonnet_4_6():
    settings = cast(Repositories, {"preferred_model": ClaudeModelId.SONNET_4_6})
    result = get_preferred_model(repo_settings=settings, is_paid=False)
    assert result == ClaudeModelId.SONNET_4_6


# --- Free user with premium models (DB setting honored regardless of tier) ---


def test_free_user_selects_opus_4_7_honored():
    settings = cast(Repositories, {"preferred_model": ClaudeModelId.OPUS_4_7})
    result = get_preferred_model(repo_settings=settings, is_paid=False)
    assert result == ClaudeModelId.OPUS_4_7


# --- Paid user with each user-selectable model ---


def test_paid_user_selects_opus_4_7():
    settings = cast(Repositories, {"preferred_model": ClaudeModelId.OPUS_4_7})
    result = get_preferred_model(repo_settings=settings, is_paid=True)
    assert result == ClaudeModelId.OPUS_4_7


def test_paid_user_selects_sonnet_4_6():
    settings = cast(Repositories, {"preferred_model": ClaudeModelId.SONNET_4_6})
    result = get_preferred_model(repo_settings=settings, is_paid=True)
    assert result == ClaudeModelId.SONNET_4_6


def test_paid_user_selects_gemini_2_5_flash():
    settings = cast(Repositories, {"preferred_model": GoogleModelId.GEMINI_2_5_FLASH})
    result = get_preferred_model(repo_settings=settings, is_paid=True)
    assert result == GoogleModelId.GEMINI_2_5_FLASH


def test_paid_user_selects_gemma_4_31b():
    settings = cast(Repositories, {"preferred_model": GoogleModelId.GEMMA_4_31B})
    result = get_preferred_model(repo_settings=settings, is_paid=True)
    assert result == GoogleModelId.GEMMA_4_31B


# --- Exhaustive: every user-selectable model works for paid users ---


def test_all_user_selectable_models_honored_for_paid():
    for model in USER_SELECTABLE_MODELS:
        settings = cast(Repositories, {"preferred_model": model.value})
        result = get_preferred_model(repo_settings=settings, is_paid=True)
        assert result == model, f"Paid user selecting {model} got {result}"


# --- Exhaustive: every free-tier model works for free users ---


def test_all_free_tier_models_honored_for_free():
    for model in FREE_TIER_MODELS:
        settings = cast(Repositories, {"preferred_model": model.value})
        result = get_preferred_model(repo_settings=settings, is_paid=False)
        assert result == model, f"Free user selecting {model} got {result}"


# --- Exhaustive: all user-selectable models honored for free users (DB overrides tier) ---


def test_all_user_selectable_models_honored_for_free():
    for model in USER_SELECTABLE_MODELS:
        settings = cast(Repositories, {"preferred_model": model.value})
        result = get_preferred_model(repo_settings=settings, is_paid=False)
        assert result == model, f"Free user selecting {model} got {result}"


# --- Exhaustive: every non-selectable model falls back for both tiers ---


def test_non_selectable_models_fallback_for_free():
    non_selectable = [
        m
        for m in (list(ClaudeModelId) + list(GoogleModelId))
        if m not in USER_SELECTABLE_MODELS
    ]
    assert len(non_selectable) > 0, "Expected at least one non-selectable model"
    for model in non_selectable:
        settings = cast(Repositories, {"preferred_model": model.value})
        result = get_preferred_model(repo_settings=settings, is_paid=False)
        assert (
            result == DEFAULT_FREE_MODEL
        ), f"Free user with non-selectable {model} should get {DEFAULT_FREE_MODEL}, got {result}"


def test_non_selectable_models_fallback_for_paid():
    non_selectable = [
        m
        for m in (list(ClaudeModelId) + list(GoogleModelId))
        if m not in USER_SELECTABLE_MODELS
    ]
    assert len(non_selectable) > 0, "Expected at least one non-selectable model"
    for model in non_selectable:
        settings = cast(Repositories, {"preferred_model": model.value})
        result = get_preferred_model(repo_settings=settings, is_paid=True)
        assert (
            result == DEFAULT_PAID_MODEL
        ), f"Paid user with non-selectable {model} should get {DEFAULT_PAID_MODEL}, got {result}"


# --- Verify constant relationships ---


def test_default_free_model_is_in_free_tier():
    assert DEFAULT_FREE_MODEL in FREE_TIER_MODELS


def test_default_paid_model_is_user_selectable():
    assert DEFAULT_PAID_MODEL in USER_SELECTABLE_MODELS


def test_free_tier_models_are_subset_of_user_selectable():
    for model in FREE_TIER_MODELS:
        assert (
            model in USER_SELECTABLE_MODELS
        ), f"{model} is free-tier but not user-selectable"
