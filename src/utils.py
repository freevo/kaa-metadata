# -----------------------------------------------------------------------------
# utils.py - Miscellaneous system utilities
# -----------------------------------------------------------------------------
# Copyright 2010-2014 Dirk Meyer, Jason Tackaberry
#
# Originally from kaa.base, (partially) ported to Python 3 by Jason Tackaberry
#
# This library is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version
# 2.1 as published by the Free Software Foundation.
#
# This library is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301 USA
# -----------------------------------------------------------------------------
import sys
import locale
import os
import getpass
import stat
from tempfile import mktemp, gettempdir

def _detect_encoding():
    """
    Find correct encoding from default locale.
    """
    # Some locales report encodings like 'utf_8_valencia' which Python doesn't
    # know.  We try stripping off the right-most parts until we find an
    # encoding that works.
    e = locale.getdefaultlocale()[1]
    while e:
        try:
            ''.encode(e)
            return e
        except LookupError:
            pass
        if '_' not in e:
            break
        e = e.rsplit('_', 1)[0]


# If encoding can't be detected from locale, default to UTF-8.
ENCODING = _detect_encoding() or 'UTF8'

def get_encoding():
    """
    Return the current encoding.
    """
    return ENCODING


def tobytes(value, encoding=None, desperate=True, coerce=False, fs=False):
    """
    Convert (if necessary) the given value to a "string of bytes", agnostic to
    any character encoding.

    :param value: the value to be converted to a string of bytes
    :param encoding: the character set to first try to encode to; if None, will
                     use the system default (from the locale).
    :type encoding: str
    :param desperate: if True and encoding to the given (or default) charset
                      fails, will also try utf-8 and latin-1 (in that order),
                      and if those fail, will encode to the preferred charset,
                      replacing unknown characters with \\\\uFFFD.
    :type desperate: bool
    :param coerce: if True, will coerce numeric types to a bytes object; if
                   False, such values will be returned untouched.
    :type coerce: bool
    :param fs: indicates value is a file name or other environment string; if True,
               the encoding (if not explicitly specified) will be the encoding
               given by ``sys.getfilesystemencoding()`` and the error handler
               used will be ``surrogateescape`` if supported.
    :type fs: bool
    :returns: the value as a bytes object, or the original value if coerce is
              False and the value was not a bytes or string.
    """
    if isinstance(value, bytes):
        # Nothing to do.
        return value
    elif isinstance(value, (int, float)):
        return bytes(str(value), 'ascii') if coerce else value
    elif not isinstance(value, str):
        # Need to coerce to a unicode before converting to bytes.  We can't just
        # feed it to bytes() in case the default character set can't encode it.
        value = tostr(value, coerce=coerce)

    errors = 'strict'
    if fs:
        if not encoding:
            encoding = sys.getfilesystemencoding()
        errors = 'surrogateescape'

    for c in (encoding or ENCODING, 'utf-8', 'latin-1'):
        try:
            return value.encode(c, errors)
        except UnicodeError:
            pass
        if not desperate:
            raise UnicodeError("Couldn't encode value to bytes (and not desperate enough to keep trying)")

    return value.encode(encoding or ENCODING, 'replace')


def tostr(value, encoding=None, desperate=True, coerce=False, fs=False):
    """
    Convert (if necessary) the given value to a unicode string.

    :param value: the value to be converted to a unicode string
    :param encoding: the character set to first try to decode as; if None, will
                     use the system default (from the locale).
    :type encoding: str
    :param desperate: if True and decoding to the given (or default) charset
                      fails, will also try utf-8 and latin-1 (in that order),
                      and if those fail, will decode as the preferred charset,
                      replacing unknown characters with \\\\uFFFD.
    :type desperate: bool
    :param coerce: if True, will coerce numeric types to a unicode string; if
                   False, such values will be returned untouched.
    :type coerce: bool
    :param fs: indicates value is a file name or other environment string; if True,
               the encoding (if not explicitly specified) will be the encoding
               given by ``sys.getfilesystemencoding()`` and the error handler
               used will be ``surrogateescape`` if supported.
    :type fs: bool
    :returns: the value as a unicode string, or the original value if coerce is
              False and the value was not a bytes or string.
    """
    if isinstance(value, str):
        # Nothing to do.
        return value
    elif isinstance(value, (int, float)):
        return str(value) if coerce else value
    elif not isinstance(value, (bytearray, bytes)):
        # Need to coerce this value.  Try the direct approach.
        try:
            return str(value)
        except UnicodeError:
            # Could be that value.__repr__ returned a non-unicode and
            # non-8bit-clean string.  Be a bit more brute force about it.
            return tostr(repr(value), desperate=desperate)

    errors = 'strict'
    if fs:
        if not encoding:
            encoding = sys.getfilesystemencoding()
        errors = 'surrogateescape'

    # We now have a bytes object to decode.
    for c in (encoding or ENCODING, 'utf-8', 'latin-1'):
        try:
            return value.decode(c, errors)
        except UnicodeError:
            pass
        if not desperate:
            raise UnicodeError("Couldn't decode value to unicode (and not desperate enough to keep trying)")

    return value.decode(encoding or ENCODING, 'replace')


def utf8(s):
    """
    Returns a UTF-8 string, converting from other character sets if
    necessary.
    """
    return tostr(s).encode('utf-8')


def fsname(s):
    """
    Return an object appropriate to represent a filename.

    :param s: the filename to decode (if needed)
    :returns: a string encoded with surrogateescape

    .. note::
       This is a convenience function, equivalent to::

           tostr(s, fs=True, desperate=False)
    """
    return tostr(s, fs=True, desperate=False)



def get_temp_path(appname):
    try:
        return get_temp_path.paths[appname]
    except KeyError:
        # create tmp directory for the user
        base = gettempdir()
        path = os.path.join(base, '{}-{}'.format(appname, getpass.getuser()))
        if not os.path.isdir(path):
            try:
                os.mkdir(path, 0o0700)
            except OSError:
                # Probably the directory already exists.  Verify.
                if not os.path.isdir(path):
                    raise IOError('Security Error: %s is not a directory, aborted' % path)

        # On non-Windows, verify the permissions.
        if sys.platform != 'win32':
            if os.path.islink(path):
                raise IOError('Security Error: %s is a link, aborted' % path)
            if stat.S_IMODE(os.stat(path).st_mode) % 0o01000 != 0o0700:
                raise IOError('Security Error: %s has wrong permissions, aborted' % path)
            if os.stat(path)[stat.ST_UID] != os.getuid():
                raise IOError('Security Error: %s does not belong to you, aborted' % path)

        get_temp_path.paths[appname] = path
        return path
get_temp_path.paths = {}


def tempfile(appname, name='', suffix='', unique=True):
    """
    Return a filename in a secure tmp directory with the given name.

    Name can also be a relative path in the temp directory, directories will
    be created if missing. If unique is set, it will return a unique name based
    on the given name.
    """
    path = get_temp_path(appname)
    name = os.path.join(path, name)
    if not os.path.isdir(os.path.dirname(name)):
        os.mkdir(os.path.dirname(name))
    if not unique:
        return name
    return mktemp(suffix=suffix, prefix=os.path.basename(name), dir=os.path.dirname(name))



def which(file, path=None):
    """
    Does what which(1) does: searches the PATH in order for a given file name
    and returns the full path to first match.
    """
    if not path:
        path = os.getenv("PATH")

    for p in path.split(":"):
        fullpath = os.path.join(p, file)
        try:
            st = os.stat(fullpath)
        except OSError:
            continue

        if sys.platform == 'win32':
            return fullpath

        # On non-Windows, ensure the file is both executable and accessible to
        # the user.
        if os.geteuid() == st[stat.ST_UID]:
            mask = stat.S_IXUSR
        elif st[stat.ST_GID] in os.getgroups():
            mask = stat.S_IXGRP
        else:
            mask = stat.S_IXOTH

        if stat.S_IMODE(st[stat.ST_MODE]) & mask:
            return fullpath

    return None


def daemonize(stdin=os.devnull, stdout=os.devnull, stderr=None,
              pidfile=None, exit=True):
    """
    Does a double-fork to daemonize the current process using the technique
    described at http://www.erlenstar.demon.co.uk/unix/faq_2.html#SEC16 .

    If exit is True (default), parent exits immediately.  If false, caller will receive
    the pid of the forked child.
    """
    # First fork.
    try:
        pid = os.fork()
        if pid > 0:
            if exit:
                # Exit from the first parent.
                sys.exit(0)

            # Wait for child to fork again (otherwise we have a zombie)
            os.waitpid(pid, 0)
            return pid
    except OSError as e:
        #log.error("Initial daemonize fork failed: %d, %s\n", e.errno, e.strerror)
        sys.exit(1)

    os.chdir("/")
    os.setsid()

    # Second fork.
    try:
        pid = os.fork()
        if pid > 0:
            # Exit from the second parent.
            sys.exit(0)
    except OSError as e:
        #log.error("Second daemonize fork failed: %d, %s\n", e.errno, e.strerror)
        sys.exit(1)

    # Create new standard file descriptors.
    if not stderr:
        stderr = stdout
    stdin = open(stdin, 'r')
    stdout = open(stdout, 'a+')
    stderr = open(stderr, 'a+', 0)
    if pidfile:
        open(pidfile, 'w+').write("%d\n" % os.getpid())

    # Remap standard fds.
    os.dup2(stdin.fileno(), sys.stdin.fileno())
    os.dup2(stdout.fileno(), sys.stdout.fileno())
    os.dup2(stderr.fileno(), sys.stderr.fileno())