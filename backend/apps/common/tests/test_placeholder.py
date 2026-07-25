"""Placeholder so pytest discovers the common test package."""


def test_common_app_importable():
    import apps.common as app_module

    assert app_module is not None
