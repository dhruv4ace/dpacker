
from . import bl_info

class DhpmEditionInfo:
    suffix = None
    name = None
    long_name = None
    marker = None

    def __init__(self, _num, _suffix, _name, _long_name, _marker, _req_markers):
        self.num = _num
        self.suffix = _suffix
        self.name = _name
        self.long_name = _long_name
        self.marker = _marker
        self.req_markers = _req_markers


bl_info_version = bl_info['version']

class DhpmVersionInfo:
    ADDON_VERSION_MAJOR = bl_info_version[0]
    ADDON_VERSION_MINOR = bl_info_version[1]
    ADDON_VERSION_PATCH = bl_info_version[2]

    ENGINE_VERSION_MAJOR = ADDON_VERSION_MAJOR
    ENGINE_VERSION_MINOR = ADDON_VERSION_MINOR
    ENGINE_VERSION_PATCH = ADDON_VERSION_PATCH

    PRESET_VERSION_FIRST_SUPPORTED = 11
    PRESET_VERSION = 14
    
    GROUPING_SCHEME_VERSION_FIRST_SUPPORTED = 1
    GROUPING_SCHEME_VERSION = 2

    RELEASE_SUFFIX = 'u1'

    @classmethod
    def release_suffix(cls):
        return cls.RELEASE_SUFFIX

    @classmethod
    def addon_version_tuple(cls):
        return (cls.ADDON_VERSION_MAJOR, cls.ADDON_VERSION_MINOR, cls.ADDON_VERSION_PATCH)

    @classmethod
    def addon_version_string(cls):
        return '{}.{}.{}'.format(cls.ADDON_VERSION_MAJOR, cls.ADDON_VERSION_MINOR, cls.ADDON_VERSION_PATCH)

    @classmethod
    def addon_version_release_string(cls):
        version_str = cls.addon_version_string()
        release_str = cls.release_suffix()

        return version_str if release_str == '' else (version_str + '-' + release_str)

    @classmethod
    def engine_version_tuple(cls):
        return (cls.ENGINE_VERSION_MAJOR, cls.ENGINE_VERSION_MINOR, cls.ENGINE_VERSION_PATCH)

    @classmethod
    def engine_version_string(cls):
        return '{}.{}.{}'.format(cls.ENGINE_VERSION_MAJOR, cls.ENGINE_VERSION_MINOR, cls.ENGINE_VERSION_PATCH)

    @classmethod
    def dhpm_edition_array(cls):
        edition_array = [
            DhpmEditionInfo(1, 's', 'std', 'STD', 'DHPM_EDITION_STANDARD', []),
            DhpmEditionInfo(2, 'p', 'pro', 'PRO', 'DHPM_EDITION_PRO', []),
            DhpmEditionInfo(3, 'd', 'demo', 'DEMO', 'DHPM_EDITION_DEMO', [])
        ]

        return edition_array
