import datetime
import io
import logging
import os.path
from pathlib import Path

import httpx
import pendulum
from PIL import Image


class Picture(object):
    # HACK: Now also handles videos, but this is not reflected in the name
    def __init__(self, data_dict, url=None, width=None, height=None) -> None:
        self.url = data_dict.get("url", url)
        if self.exists():
            self.ext = self.url.split('.')[-1]
        self.width = data_dict.get("width", width)
        self.height = data_dict.get("height", height)
        self.date = None
        self.data = None

    def __repr__(self) -> str:
        return f"<Image {self.url} {self.width}x{self.height}>"

    def exists(self):
        return self.url is not None

    def download(self, path: Path | None, skip_existing: bool = True) -> bytes | None:
        """
        path: Path to save the image to (without extension). If None, the image is not saved.
        """
        self.ext = self.ext
        ext_type = self.ext
        _path = path.with_suffix(f".{ext_type}") if path else None

        # don't re-download already saved pictures
        if _path and _path.exists() and skip_existing:
            logging.debug(f"Skipping already-downloaded {self.url}")
            return

        r = httpx.get(self.url, headers={
            "user-agent": "BeReal/1.0.1 (AlexisBarreyat.BeReal; build:9513; iOS 16.0.2) 1.0.0/BRApriKit",
            "x-ios-bundle-identifier": "AlexisBarreyat.BeReal"})

        self.data = r.content

        if _path:
            _path.write_bytes(self.data)
            logging.debug(f"Downloaded {self.url}")

        return r.content

    def get_date(self):
        if self.date:
            return self.date
        r = httpx.head(self.url)

        # https://stackoverflow.com/a/71637523
        if r.status_code != 200:
            raise Exception(f"Error requesting image: {r.status_code}")

        url_time = r.headers.get('Last-Modified')
        last_updated_pattern = "%a, %d %b %Y %H:%M:%S %Z"
        timestamp = int(datetime.datetime.strptime(url_time, last_updated_pattern).timestamp())
        self.date = pendulum.from_timestamp(timestamp)
        return self.date
