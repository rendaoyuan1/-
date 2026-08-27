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
    "/旧版/",
    "(备用)",
    "备用版",
    "暂不能用",
    "第一版",
    "初始版",
    "Ver.1",
    "Ver.2",
]

VERSION_RE = re.compile(r"(?:\s+v?|\()(?P<v>\d+(?:\.\d+){0,3})(?:\)|\s|$)", re.I)


def fetch_json(url):
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "musicfree-auto-sync",
            "Accept": "application/vnd.github+json",
        },
    )
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
    stem = filename[:-3]
    stem = re.sub(r"\s+[vV]?\d+(?:\.\d+){0,3}.*$", "", stem).strip()
    return f"{directory}/{stem}".lower()


def display_name(path):
    filename = path.rsplit("/", 1)[-1][:-3]
    filename = re.sub(r"\s+[vV]?\d+(?:\.\d+){0,3}.*$", "", filename).strip()
    parent = path.split("/")[0] if "/" in path else ""
    if filename.lower() in {"qq", "youtube", "bilibili", "migu", "kugou", "kuwo", "netease", "webdav", "navidrome"}:
        return f"{parent}-{filename}" if parent else filename
    return filename


def raw_url(path):
    return f"https://raw.githubusercontent.com/{SOURCE_REPO}/{SOURCE_BRANCH}/" + quote(path, safe="/()[],-._")


def select_latest(paths, predicate):
    matches = [p for p in paths if predicate(p)]
    if not matches:
        return None
    return max(matches, key=lambda p: (version_tuple(p), p.lower()))


def generate_four_pack(candidates):
    safe = [p for p in candidates if "vip" not in p.lower() and "会员" not in p]

    netease = select_latest(
        safe,
        lambda p: p.startswith("sinmite/") and p.rsplit("/", 1)[-1].lower().startswith("netease ") and "netease_fm" not in p.lower(),
    )
    kuwo = select_latest(
        safe,
        lambda p: p.startswith("sinmite/") and p.rsplit("/", 1)[-1].lower().startswith("kuwo "),
    )
    qq = select_latest(
        safe,
        lambda p: p.startswith("猫头猫(MF开发者)/") and p.rsplit("/", 1)[-1].lower().startswith("qq "),
    )

    plugins = []
    if netease:
        plugins.append({"name": "网易云音乐", "url": raw_url(netease), "version": version_text(netease)})

    # 使用当前公开 MusicFree 聚合源中仍在维护的汽水插件地址。
    plugins.append({
        "name": "汽水音乐",
        "url": "https://gitee.com/hongmengv5/musicfree/raw/master/qishui.js",
        "version": "0.1.5",
    })

    if kuwo:
        plugins.append({"name": "酷我音乐", "url": raw_url(kuwo), "version": version_text(kuwo)})
    if qq:
        plugins.append({"name": "QQ音乐", "url": raw_url(qq), "version": version_text(qq)})

    with open(FOUR_PACK_OUTPUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump({"plugins": plugins}, f, ensure_ascii=False, indent=2)
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

    plugins = []
    for path in sorted(selected.values(), key=lambda p: p.lower()):
        plugins.append({
            "name": display_name(path),
            "url": raw_url(path),
            "version": version_text(path),
        })

    with open(OUTPUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump({"plugins": plugins}, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"Generated {OUTPUT} with {len(plugins)} plugins")
    generate_four_pack(candidates)


if __name__ == "__main__":
    main()
