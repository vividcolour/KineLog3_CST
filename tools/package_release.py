#!/usr/bin/env python3
"""Build the end-user download: dist/Color-Space-Transform-mk2-v<VERSION>.zip (+ .sha256).

    python3 tools/package_release.py
"""
import hashlib, os, stat, zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERSION = open(os.path.join(ROOT, 'VERSION')).read().strip()
TOP = f'Color-Space-Transform-mk2-v{VERSION}'

FILES = [  # (source relative to repo, path inside the zip, executable)
    ('dctl/Color Space Transform mk2.dctl', 'Color Space Transform mk2.dctl', False),
    ('dctl/Color Remap mk2.dctl', 'Color Remap mk2.dctl', False),
    ('extras/kinelog3-to-logc3/KineLog3_to_LogC3.dctl', 'Extras/KineLog3_to_LogC3.dctl', False),
    ('extras/kinelog3-to-logc3/KineLog3_KWG_to_LogC3_AWG3_EI800.cube', 'Extras/KineLog3_KWG_to_LogC3_AWG3_EI800.cube', False),
    ('installers/install-macos.command', 'install-macos.command', True),
    ('installers/uninstall-macos.command', 'uninstall-macos.command', True),
    ('installers/install-windows.bat', 'install-windows.bat', False),
    ('installers/uninstall-windows.bat', 'uninstall-windows.bat', False),
    ('installers/install-linux.sh', 'install-linux.sh', True),
    ('installers/READ_ME_FIRST.txt', 'READ ME FIRST.txt', False),
    ('LICENSE', 'LICENSE.txt', False),
]


def main():
    dist = os.path.join(ROOT, 'dist')
    os.makedirs(dist, exist_ok=True)
    out = os.path.join(dist, f'{TOP}.zip')
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for src, dst, exe in FILES:
            data = open(os.path.join(ROOT, src), 'rb').read()
            if src.endswith('READ_ME_FIRST.txt'):
                data = data.decode().replace('__VERSION__', VERSION).replace('\r\n', '\n').replace('\n', '\r\n').encode()
            info = zipfile.ZipInfo(f'{TOP}/{dst}', date_time=(2026, 1, 1, 0, 0, 0))
            info.external_attr = ((0o755 if exe else 0o644) | stat.S_IFREG) << 16  # keep exec bit for macOS
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3  # unix, so permissions are honoured
            z.writestr(info, data)
    digest = hashlib.sha256(open(out, 'rb').read()).hexdigest()
    open(out + '.sha256', 'w').write(f'{digest}  {os.path.basename(out)}\n')
    print(out)
    print('sha256', digest)


if __name__ == '__main__':
    main()
