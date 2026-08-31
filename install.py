# Installer for the WeeWX rtspimage extension.
# Copyright 2026 Zach Taffet
# Distributed under the terms of the GNU General Public License v3 (GPLv3).

from weecfg.extension import ExtensionInstaller


def loader():
    return RTSPImageInstaller()


class RTSPImageInstaller(ExtensionInstaller):
    def __init__(self):
        super().__init__(
            version="0.1.0",
            name="rtspimage",
            description="Capture still images from RTSP camera feeds using ffmpeg.",
            author="Zach Taffet",
            author_email="152570+ziti@users.noreply.github.com",
            config={
                "StdReport": {
                    "rtspimage": {
                        "skin": "rtspimage",
                        "enable": "true",
                        "ffmpeg_path": "ffmpeg",
                        "rtsp_transport": "tcp",
                        "timeout": "30",
                        "quality": "2",
                        "cameras": {
                            "cam01": {
                                "url": "rtsp://user:password@camera.example:8554/ch1",
                                "destinations": "/var/www/html/belchertown/cam01.jpg",
                            },
                        },
                    },
                },
            },
            files=[
                ("bin/user", ["bin/user/rtspimage.py"]),
                ("skins/rtspimage", ["skins/rtspimage/skin.conf"]),
            ],
        )
