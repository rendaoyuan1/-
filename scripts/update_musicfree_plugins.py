import json
import re
import urllib.request
from urllib.parse import quote

SOURCE_REPO = "TZB679/USEFUL-MF-PLUG-INS"
SOURCE_BRANCH = "main"
OUTPUT = "musicfree-unified-plugins.json"
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

# 同一插件有多个版本时，用去掉版本号后的路径作为分组键，优先保留版本号更高的文件。
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
    nums = matches[-1].group("v").split(".")
    return tuple(int(x) for x in nums)


def version_text(path):
    matches = list(VERSION_RE.finditer(path))
    return matches[-1].group("v") if matches else "current"


def group_key(path):
    # 仅在同一目录中合并同名不同版本，避免 QQ / 网易云等不同作者插件互相覆盖。
    directory, filename = path.rsplit("/", 1) if "/" in path else ("", path)
    stem = filename[:-3]
    stem = re.sub(r"\s+[vV]?\d+(?:\.\d+){0,3}.*$", "", stem).strip()
    return f"{directory}/{stem}".lower()


def display_name(path):
    filename = path.rsplit("/", 1)[-1][:-3]
    filename = re.sub(r"\s+[vV]?\d+(?:\.\d+){0,3}.*$", "", filename).strip()
    parent = path.split("/")[0] if "/" in path else ""
    # 为常见重复名称加来源前缀，导入后更容易区分。
    if filename.lower() in {"qq", "youtube", "bilibili", "migu", "kugou", "kuwo", "netease", "webdav", "navidrome"}:
        return f"{parent}-{filename}" if parent else filename
    return filename


def raw_url(path):
    return f"https://raw.githubusercontent.com/{SOURCE_REPO}/{SOURCE_BRANCH}/" + quote(path, safe="/()[],-._")


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

    output = {"plugins": plugins}
    with open(OUTPUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"Generated {OUTPUT} with {len(plugins)} plugins")


if __name__ == "__main__":
    main()
