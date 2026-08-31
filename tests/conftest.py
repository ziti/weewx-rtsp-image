"""Test bootstrap for the rtspimage extension.

``bin/user/rtspimage.py`` imports ``weewx`` / ``weeutil`` at module load time.
Neither is needed to unit-test the file's logic, so this module:

* puts ``bin/`` on ``sys.path`` so ``import user.rtspimage`` works, and
* installs minimal stubs for ``weewx`` / ``weewx.reportengine`` /
  ``weeutil.weeutil`` -- but only when a real WeeWX is not importable (CI runs
  a separate integration job against a real install).
"""

import os
import sys
import types

BIN_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, "bin"))
if BIN_DIR not in sys.path:
    sys.path.insert(0, BIN_DIR)


def _ensure_weewx_stubs():
    try:
        import weewx  # noqa: F401
        import weewx.reportengine  # noqa: F401
        from weeutil.weeutil import option_as_list, to_bool  # noqa: F401

        return  # a real WeeWX is importable; use it
    except ImportError:
        pass

    weewx = types.ModuleType("weewx")
    weewx.__version__ = "0.0.0-stub"
    weewx.debug = 0

    reportengine = types.ModuleType("weewx.reportengine")

    class ReportGenerator:
        def __init__(self, config_dict=None, skin_dict=None, gen_ts=None,
                     first_run=None, stn_info=None, record=None):
            self.config_dict = config_dict or {}
            self.skin_dict = skin_dict or {}
            self.gen_ts = gen_ts
            self.first_run = first_run
            self.stn_info = stn_info
            self.record = record

    reportengine.ReportGenerator = ReportGenerator
    weewx.reportengine = reportengine

    weeutil = types.ModuleType("weeutil")
    weeutil_weeutil = types.ModuleType("weeutil.weeutil")

    def to_bool(value):
        if isinstance(value, bool):
            return value
        try:
            if value.lower() in ("true", "yes", "y", "1", "on"):
                return True
            if value.lower() in ("false", "no", "n", "0", "off"):
                return False
        except AttributeError:
            pass
        try:
            return bool(int(value))
        except (ValueError, TypeError):
            pass
        raise ValueError("Unknown boolean specifier: '%s'." % (value,))

    def option_as_list(option):
        if option is None:
            return []
        if isinstance(option, (list, tuple)):
            return list(option)
        return [option]

    weeutil_weeutil.to_bool = to_bool
    weeutil_weeutil.option_as_list = option_as_list
    weeutil.weeutil = weeutil_weeutil

    for name, mod in (
        ("weewx", weewx),
        ("weewx.reportengine", reportengine),
        ("weeutil", weeutil),
        ("weeutil.weeutil", weeutil_weeutil),
    ):
        sys.modules[name] = mod


_ensure_weewx_stubs()
