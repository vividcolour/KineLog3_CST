#!/usr/bin/env python3
"""Build the release downloads into dist/:

    Color-Space-Transform-mk2.dctl            the main DCTL, ready to drop into Resolve's LUT folder
    Color-Remap-mk2.dctl                      the one-node Kinefinity / DJI remap DCTL
    Color-Space-Transform-mk2-Installer.zip   both DCTLs + extras + one-click macOS / Windows / Linux installers
    Color-Space-Transform-mk2-DCTL-only.zip   both DCTLs + extras, no scripts (manual install)
    SHA256SUMS.txt                            checksums of all of the above

File names carry no version number so README links to releases/latest/download/<name> never break.

    python3 tools/package_release.py
"""
import hashlib, os, shutil, stat, zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERSION = open(os.path.join(ROOT, 'VERSION')).read().strip()
TOP = f'Color-Space-Transform-mk2-v{VERSION}'

DCTLS = [  # (source, name inside zips / Resolve, standalone release asset name)
    ('dctl/Color Space Transform mk2.dctl', 'Color Space Transform mk2.dctl', 'Color-Space-Transform-mk2.dctl'),
    ('dctl/Color Remap mk2.dctl', 'Color Remap mk2.dctl', 'Color-Remap-mk2.dctl'),
]
EXTRAS = [
    ('extras/kinelog3-to-logc3/KineLog3_to_LogC3.dctl', 'Extras/KineLog3_to_LogC3.dctl', False),
    ('extras/kinelog3-to-logc3/KineLog3_KWG_to_LogC3_AWG3_EI800.cube', 'Extras/KineLog3_KWG_to_LogC3_AWG3_EI800.cube', False),
    ('LICENSE', 'LICENSE.txt', False),
]
INSTALLER_ONLY = [
    ('installers/install-macos.command', 'install-macos.command', True),
    ('installers/uninstall-macos.command', 'uninstall-macos.command', True),
    ('installers/install-windows.bat', 'install-windows.bat', False),
    ('installers/uninstall-windows.bat', 'uninstall-windows.bat', False),
    ('installers/install-linux.sh', 'install-linux.sh', True),
    ('installers/READ_ME_FIRST.txt', 'READ ME FIRST.txt', False),
]
DCTL_ONLY = [('installers/READ_ME_DCTL_ONLY.txt', 'READ ME FIRST.txt', False)]


def _txt(data):
    return data.decode().replace('__VERSION__', VERSION).replace('\r\n', '\n').replace('\n', '\r\n').encode()


def _zip(path, entries):
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for src, dst, exe in entries:
            data = open(os.path.join(ROOT, src), 'rb').read()
            if src.endswith('.txt'):
                data = _txt(data)
            info = zipfile.ZipInfo(f'{TOP}/{dst}', date_time=(2026, 1, 1, 0, 0, 0))  # fixed date: reproducible
            info.external_attr = ((0o755 if exe else 0o644) | stat.S_IFREG) << 16    # keep exec bit for macOS
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3  # unix, so permissions are honoured
            z.writestr(info, data)


def main():
    dist = os.path.join(ROOT, 'dist')
    shutil.rmtree(dist, ignore_errors=True)
    os.makedirs(dist)
    dctl_entries = [(src, name, False) for src, name, _ in DCTLS]
    outputs = []
    for src, _, asset in DCTLS:
        shutil.copyfile(os.path.join(ROOT, src), os.path.join(dist, asset))
        outputs.append(asset)
    for name, extra in (('Color-Space-Transform-mk2-Installer.zip', INSTALLER_ONLY),
                        ('Color-Space-Transform-mk2-DCTL-only.zip', DCTL_ONLY)):
        _zip(os.path.join(dist, name), dctl_entries + EXTRAS + extra)
        outputs.append(name)
    sums = ''.join(f'{hashlib.sha256(open(os.path.join(dist, n), "rb").read()).hexdigest()}  {n}\n' for n in outputs)
    open(os.path.join(dist, 'SHA256SUMS.txt'), 'w').write(sums)
    print(f'v{VERSION} ->', dist)
    print(sums, end='')


if __name__ == '__main__':
    main()
