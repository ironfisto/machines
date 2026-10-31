#!/usr/bin/env python3
"""Install one file from a repo's latest GitHub release. Uses only the standard library."""
import argparse
import gzip
import json
import os
import platform
import re
import shutil
import stat
import sys
import tarfile
import tempfile
import urllib.request
import zipfile

ARCHES = {"x86_64": ("amd64", "x86_64"), "amd64": ("amd64", "x86_64"),
          "aarch64": ("arm64", "aarch64"), "arm64": ("arm64", "aarch64")}


def fetch(url, accept=None):
    headers = {"User-Agent": "htb-setup"}
    if accept:
        headers["Accept"] = accept
    token = os.environ.get("GITHUB_TOKEN")
    if token and url.startswith("https://api.github.com/"):
        headers["Authorization"] = f"Bearer {token}"
    return urllib.request.urlopen(urllib.request.Request(headers=headers, url=url), timeout=120)


def find_asset(repo, pattern, machine):
    arch, xarch = ARCHES[machine]
    regex = pattern.replace("{arch}", arch).replace("{xarch}", xarch)
    with fetch(f"https://api.github.com/repos/{repo}/releases/latest",
               "application/vnd.github+json") as response:
        assets = json.load(response)["assets"]
    matches = [a for a in assets if re.search(regex, a["name"])]
    if not matches:
        names = ", ".join(a["name"] for a in assets)
        raise SystemExit(f"{repo}: no asset matches {regex!r}. Available: {names}")
    return matches[0]


def member_matches(path, member):
    path = path.replace("\\", "/")
    return path == member or path.endswith("/" + member)


def extract(archive, asset_name, member, output):
    """Copy the wanted file to output. Only that file is read, so archive paths are never used."""
    if asset_name.endswith(".zip"):
        with zipfile.ZipFile(archive) as zipped:
            for name in zipped.namelist():
                if member_matches(name, member):
                    with zipped.open(name) as src, open(output, "wb") as dst:
                        shutil.copyfileobj(src, dst)
                    return
            # RustScan ships a tar.gz inside a zip.
            for name in zipped.namelist():
                if name.endswith((".tar.gz", ".tgz")):
                    with zipped.open(name) as src, tempfile.NamedTemporaryFile() as inner:
                        shutil.copyfileobj(src, inner)
                        inner.flush()
                        extract(inner.name, name, member, output)
                        return
    elif asset_name.endswith((".tar.gz", ".tgz")):
        with tarfile.open(archive) as tar:
            for entry in tar.getmembers():
                if entry.isfile() and member_matches(entry.name, member):
                    with tar.extractfile(entry) as src, open(output, "wb") as dst:
                        shutil.copyfileobj(src, dst)
                    return
    elif asset_name.endswith(".gz"):
        with gzip.open(archive) as src, open(output, "wb") as dst:
            shutil.copyfileobj(src, dst)
        return
    else:
        shutil.copyfile(archive, output)
        return
    raise SystemExit(f"{asset_name}: {member} not found in archive")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repo")
    parser.add_argument("pattern")
    parser.add_argument("--name")
    parser.add_argument("--member")
    parser.add_argument("--dest", default="/usr/local/bin")
    parser.add_argument("--arch", default=platform.machine().lower())
    parser.add_argument("--dry-run", action="store_true", help="print the matched asset only")
    args = parser.parse_args()

    if args.arch not in ARCHES:
        raise SystemExit(f"Unsupported architecture: {args.arch}")

    asset = find_asset(args.repo, args.pattern, args.arch)
    if args.dry_run:
        print(asset["name"])
        return

    output = os.path.join(args.dest, args.name)
    os.makedirs(args.dest, exist_ok=True)
    with tempfile.TemporaryDirectory() as workdir:
        download = os.path.join(workdir, "asset")
        with fetch(asset["browser_download_url"]) as response, open(download, "wb") as dst:
            shutil.copyfileobj(response, dst)
        staged = os.path.join(workdir, "staged")
        extract(download, asset["name"], args.member or args.name, staged)
        shutil.copyfile(staged, output)
    os.chmod(output, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
    print(f"Installed {output} from {asset['name']}")


if __name__ == "__main__":
    sys.exit(main())
