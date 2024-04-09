from kodi_six import xbmcaddon
from kodi_six.utils import py2_decode
import six


ADDON = xbmcaddon.Addon()
ADDON_ID = ADDON.getAddonInfo("id")
ADDON_NAME = ADDON.getAddonInfo("name")
ADDON_ICON = ADDON.getAddonInfo("icon")
ADDON_VERSION = ADDON.getAddonInfo("version")

# Borrowed from xbmcswift2
def get_setting(key, converter=str, choices=None):
    value = ADDON.getSetting(id=key)
    if isinstance(choices, (list, tuple)):
        return choices[int(value)]
    elif converter is six.text_type or converter is str:
        return py2_decode(value)
    elif converter is bool:
        return value == 'true'
    elif converter is int:
        return int(value)
    else:
        raise TypeError('Acceptable converters are str, unicode, bool and '
                        'int. Acceptable choices are instances of list '
                        ' or tuple.')
    

def set_setting(key, val):
    return ADDON.setSetting(id=key, value=val)