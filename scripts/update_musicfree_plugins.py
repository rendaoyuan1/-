import json
import re
import urllib.request
from urllib.parse import quote

SOURCE_REPO = "TZB679/USEFUL-MF-PLUG-INS"
SOURCE_BRANCH = "main"
OUTPUT = "musicfree-unified-plugins.json"
FOUR_PACK_OUTPUT = "musicfree-4pack.json"
TREE_API = f"https://api.github.com/repos/{SOURCE_REPO}/git/trees/{SOURCE_BRANCH}?recursive=1"

EXCLUDE_MARKERS = [
    "/旧版/", "(备用)", "备用版", "暂不能用", "第一版", "初始版", "Ver.1", "Ver.2",
]
VERSION_RE = re.compile(r"(?:\s+v?|\()(?P<v>\d+(?:\.\d+){0,3})(?:\)|\s|$)", re.I)


def fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "musicfree-auto-sync", "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def version_tuple(path):
    matches = list(VERSION_RE.finditer(path))
    if not matches:
        return (0,)
    return tuple(int(x) for x in matches[-1].group("v").split("."))


def version_text(path):
    matches = list(VERSION_RE.finditer(path))
    return matches[-1].group("v") if matches else "current"


def group_key(path):
    directory, filename = path.rsplit("/", 1) if "/" in path else ("", path)
    stem = re.sub(r"\s+[vV]?\d+(?:\.\d+){0,3}.*$", "", filename[:-3]).strip()
    return f"{directory}/{stem}".lower()


def display_name(path):
    filename = re.sub(r"\s+[vV]?\d+(?:\.\d+){0,3}.*$", "", path.rsplit("/", 1)[-1][:-3]).strip()
    parent = path.split("/")[0] if "/" in path else ""
    if filename.lower() in {"qq", "youtube", "bilibili", "migu", "kugou", "kuwo", "netease", "webdav", "navidrome"}:
        return f"{parent}-{filename}" if parent else filename
    return filename


def raw_url(path):
    return f"https://raw.githubusercontent.com/{SOURCE_REPO}/{SOURCE_BRANCH}/" + quote(path, safe="/()[],-._")


def generate_four_pack():
    # 四源包使用单独的稳定公开维护源，避免每天又切回旧插件。
    plugins = [
        {
            "name": "网易云音乐（稳定源）",
            "url": "https://cdn.jsdelivr.net/gh/qwerwhr/musicfree-plugins@main/网易云音乐%20（非VIP）.js",
            "version": "stable",
        },
        {
            "name": "汽水音乐（GitHub源）",
            "url": "https://cdn.jsdelivr.net/gh/qwerwhr/musicfree-plugins@main/汽水qishui音乐.js",
            "version": "stable",
        },
        {
            "name": "酷我音乐（稳定源）",
            "url": "https://cdn.jsdelivr.net/gh/qwerwhr/musicfree-plugins@main/云音乐%20（酷我非VIP）.js",
            "version": "stable",
        },
        {
            "name": "QQ音乐（稳定源）",
            "url": "https://cdn.jsdelivr.net/gh/qwerwhr/musicfree-plugins@main/QQ音乐%20（非VIP）.js",
            "version": "stable",
        },
    ]
    with open(FOUR_PACK_OUTPUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump({"desc": "网易云、汽水、酷我、QQ 四源稳定版", "plugins": plugins}, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"Generated {FOUR_PACK_OUTPUT} with {len(plugins)} plugins")


def main():
    tree = fetch_json(TREE_API)
    candidates = []
    for item in tree.get("tree", []):
        path = item.get("path", "")
        if item.get("type") != "blob" or not path.lower().endswith(".js"):
            continue
        if any(marker in path for marker in EXCLUDE_MARKERS):
            continue
        candidates.append(path)

    selected = {}
    for path in candidates:
        key = group_key(path)
        current = selected.get(key)
        if current is None or version_tuple(path) > version_tuple(current):
            selected[key] = path

    plugins = [{"name": display_name(path), "url": raw_url(path), "version": version_text(path)}
               for path in sorted(selected.values(), key=lambda p: p.lower())]

    with open(OUTPUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump({"plugins": plugins}, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"Generated {OUTPUT} with {len(plugins)} plugins")
    generate_four_pack()


if __name__ == "__main__":
    main()
