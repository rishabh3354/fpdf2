# -*- coding: utf-8 -*-

import re
import struct
import zlib
from six import BytesIO

from PIL import Image

from .errors import fpdf_error
from .php import substr
from .py3k import PY3K, b
from .util import freadint as read_integer
from six.moves.urllib.request import urlopen


def load_resource(filename, reason = "image"):
    """Load external file"""
    # if a bytesio instance is passed in, use it as is.
    if isinstance(filename, BytesIO):
       return filename
    # by default loading from network is allowed for all images
    if reason == "image":
        if filename.startswith("http://") or \
           filename.startswith("https://"):
            f = BytesIO(urlopen(filename).read())
        else:
            with open(filename, "rb") as fl:
                f = BytesIO(fl.read())
        return f
    else:
        fpdf_error("Unknown resource loading reason \"%s\"" % reason)

def get_img_info(bytesio):
    img = Image.open(bytesio)
    if img.mode not in ['L', 'LA', 'RGBA']:
        img = img.convert('RGBA')
    w, h = img.size
    info = {}
    if img.mode in ('L', 'LA'):
        dpn, bpc, colspace = 1, 8, 'DeviceGray'
        info['data'] = to_zdata(img, slice(0, 1))
        if img.mode == 'LA':
            info['smask'] = to_zdata(img, slice(1, 2))
    else:  # RGBA image
        dpn, bpc, colspace = 3, 8, 'DeviceRGB'
        info['data'] = to_zdata(img, slice(0, 3))
        info['smask'] = to_zdata(img, slice(3, 4))

    dp = '/Predictor 15 /Colors ' + str(dpn) + ' /BitsPerComponent '+str(bpc)+' /Columns '+str(w)+''

    info.update({
        'w': w,
        'h': h,
        'cs': colspace,
        'bpc': bpc,
        'f': 'FlateDecode',
        'dp': dp,
        'pal': '',
        'trns': '',
    })

    return info


def to_zdata(img, slice_=slice(0, None)):
    is_single_channel = isinstance(img.getdata()[0], int)
    assert not is_single_channel or slice_ in (slice(0, None), slice(0, 1)), 'Single-channel images cannot be sliced'
    data = b''
    for i, px in enumerate(img.getdata()):
        if i % img.size[0] == 0:
            data += b'\0'
        data += bytes([px] if is_single_channel else px[slice_])
    return zlib.compress(data)
