"""由主题元数据生成全局去重的文献目录和 BibTeX 数据库。"""

import argparse
import hashlib
import re
import unicodedata
from collections import defaultdict
from pathlib import Path
from urllib.parse import unquote

import yaml

PROJECT = Path(__file__).resolve().parents[1]
METADATA_DIR = Path("reference/literature/metadata")
CATALOG_PATH = Path("reference/literature/catalog.yaml")
BIB_PATH = Path("reference/literature/hazardcast.bib")
CORE_FIELDS = (
    "title",
    "authors",
    "year",
    "venue",
    "doi",
    "url",
    "oa_url",
    "methods",
    "datasets",
    "metrics",
    "relevance",
    "verified_at",
)
STOP_WORDS = {"a", "an", "and", "for", "from", "in", "of", "on", "the", "to", "using", "with"}
CONFERENCE_MARKERS = (
    "conference",
    "proceedings",
    "workshop",
    "neurips",
    "nips",
    "iclr",
    "icml",
    "cvpr",
    "iccv",
    "icassp",
    "sc20",
)
JOURNAL_SERIALS = (
    "proceedings of the aaai conference on artificial intelligence",
    "proceedings of the aaai symposium series",
    "proceedings of the national academy of sciences",
)


def normalize_doi(value):
    """把 DOI 或 DOI URL 转成可比较的小写规范形式。"""
    if value is None or not str(value).strip():
        return None
    doi = unquote(str(value).strip())
    doi = re.sub(r"^doi:\s*", "", doi, flags=re.IGNORECASE)
    doi = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", doi, flags=re.IGNORECASE)
    return doi.strip().rstrip(".").casefold()


def normalize_title(value):
    """忽略标题的大小写、重音、标点和空白差异。"""
    decomposed = unicodedata.normalize("NFKD", str(value))
    unaccented = "".join(character for character in decomposed if not unicodedata.combining(character))
    return " ".join("".join(character if character.isalnum() else " " for character in unaccented).casefold().split())


def load_sources(root):
    """读取所有主题 YAML，并保留主题和原始条目 ID。"""
    sources = []
    metadata_dir = root / METADATA_DIR
    paths = sorted(metadata_dir.glob("*.yaml"))
    if not paths:
        raise ValueError(f"未找到主题元数据：{metadata_dir}")
    for path in paths:
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(document, dict) or not isinstance(document.get("papers"), list):
            raise ValueError(f"无效的主题元数据：{path}")
        topic = document.get("topic")
        if topic != path.stem:
            raise ValueError(f"主题名与文件名不一致：{path}")
        topic_file = Path("reference/literature/topics") / f"{topic}.md"
        if not (root / topic_file).is_file():
            raise ValueError(f"缺少主题综述：{root / topic_file}")
        seen_ids = set()
        for paper in document["papers"]:
            source_id = paper.get("id")
            if not source_id or source_id in seen_ids:
                raise ValueError(f"主题内条目 ID 缺失或重复：{topic}/{source_id}")
            seen_ids.add(source_id)
            if not paper.get("title") or not paper.get("authors") or not paper.get("year"):
                raise ValueError(f"条目缺少标题、作者或年份：{topic}/{source_id}")
            if bool(paper.get("pdf_path")) != bool(paper.get("sha256")):
                raise ValueError(f"PDF 路径和 SHA-256 必须同时填写：{topic}/{source_id}")
            sources.append(
                {
                    "topic": topic,
                    "source_id": source_id,
                    "metadata": (METADATA_DIR / path.name).as_posix(),
                    "topic_file": topic_file.as_posix(),
                    "paper": paper,
                }
            )
    return sources


def group_sources(sources):
    """按 DOI 和标题两个等价关系合并来源记录。"""
    parent = list(range(len(sources)))

    def find(index):
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    def union(left, right):
        left_root, right_root = find(left), find(right)
        if left_root != right_root:
            parent[max(left_root, right_root)] = min(left_root, right_root)

    for normalizer, field in ((normalize_doi, "doi"), (normalize_title, "title")):
        seen = {}
        for index, source in enumerate(sources):
            key = normalizer(source["paper"].get(field))
            if key is None:
                continue
            if key in seen:
                union(index, seen[key])
            else:
                seen[key] = index

    groups = defaultdict(list)
    for index, source in enumerate(sources):
        groups[find(index)].append(source)

    for grouped in groups.values():
        titles = {normalize_title(source["paper"]["title"]) for source in grouped}
        if len(titles) != 1:
            raise ValueError(f"同一 DOI 对应了不同标题：{sorted(titles)}")
        by_title = defaultdict(set)
        for source in grouped:
            doi = normalize_doi(source["paper"].get("doi"))
            if doi:
                by_title[normalize_title(source["paper"]["title"])].add(doi)
        if any(len(dois) > 1 for dois in by_title.values()):
            raise ValueError(f"同一标题对应了不同 DOI：{grouped[0]['paper']['title']}")
    return list(groups.values())


def ascii_words(value):
    """生成 BibTeX key 使用的 ASCII 单词序列。"""
    decomposed = unicodedata.normalize("NFKD", str(value))
    unaccented = "".join(character for character in decomposed if not unicodedata.combining(character))
    return re.findall(r"[a-z0-9]+", unaccented.casefold())


def bibtex_base_key(paper):
    """从第一作者、年份和首个实义标题词构造稳定 key 前缀。"""
    author_words = ascii_words(paper["authors"][0])
    surname_words = ascii_words(str(paper["authors"][0]).split()[-1])
    title_words = [word for word in ascii_words(paper["title"]) if word not in STOP_WORDS]
    surname = "".join(surname_words) or (author_words[-1] if author_words else "anonymous")
    title_word = title_words[0] if title_words else "untitled"
    return f"{surname}{paper['year']}{title_word}"


def first_present(grouped, field):
    """按固定的主题和 ID 顺序选取首个非空字段。"""
    for source in grouped:
        value = source["paper"].get(field)
        if value is not None:
            return value
    return None


def canonical_paper(grouped, key):
    """保留规范书目信息、全部主题交叉引用及本地 PDF 副本。"""
    grouped = sorted(grouped, key=lambda source: (source["topic"], source["source_id"]))
    primary = grouped[0]["paper"]
    paper = {"id": key}
    for field in CORE_FIELDS:
        value = first_present(grouped, field)
        if field == "doi":
            value = normalize_doi(value)
        elif field == "verified_at" and value is not None:
            value = str(value)
        paper[field] = value

    pdf_with_source = [
        source for source in grouped if source["paper"].get("pdf_path")
    ]
    access_source = pdf_with_source[0]["paper"] if pdf_with_source else primary
    paper["access"] = access_source.get("access")
    paper["pdf_path"] = access_source.get("pdf_path")
    paper["sha256"] = access_source.get("sha256")
    paper["topics"] = sorted({source["topic"] for source in grouped})
    paper["sources"] = []
    copies = {}
    for source in grouped:
        original = source["paper"]
        paper["sources"].append(
            {
                "topic": source["topic"],
                "id": source["source_id"],
                "metadata": source["metadata"],
                "topic_file": source["topic_file"],
                "doi": original.get("doi"),
                "url": original.get("url"),
                "oa_url": original.get("oa_url"),
                "pdf_path": original.get("pdf_path"),
                "sha256": original.get("sha256"),
            }
        )
        if original.get("pdf_path"):
            path = original["pdf_path"]
            sha256 = original["sha256"].casefold()
            if path in copies and copies[path] != sha256:
                raise ValueError(f"同一 PDF 对应了不同 SHA-256：{path}")
            copies[path] = sha256
    paper["pdf_copies"] = [
        {"path": path, "sha256": copies[path]} for path in sorted(copies)
    ]
    return paper


def build_catalog(root=PROJECT):
    """构建不含时间戳、输入顺序无关的规范目录。"""
    sources = load_sources(Path(root))
    groups = group_sources(sources)
    bases = []
    for grouped in groups:
        ordered = sorted(grouped, key=lambda source: (source["topic"], source["source_id"]))
        merged = {field: first_present(ordered, field) for field in ("title", "authors", "year", "doi")}
        bases.append(bibtex_base_key(merged))
    base_counts = {base: bases.count(base) for base in set(bases)}
    keyed_groups = []
    for base, grouped in zip(bases, groups, strict=True):
        ordered = sorted(grouped, key=lambda source: (source["topic"], source["source_id"]))
        identity = normalize_doi(first_present(ordered, "doi")) or normalize_title(ordered[0]["paper"]["title"])
        suffix = f"-{hashlib.sha256(identity.encode('utf-8')).hexdigest()[:8]}" if base_counts[base] > 1 else ""
        keyed_groups.append((f"{base}{suffix}", ordered))
    papers = [canonical_paper(grouped, key) for key, grouped in sorted(keyed_groups)]
    pdf_count = len({copy["path"] for paper in papers for copy in paper["pdf_copies"]})
    papers_with_pdf = sum(bool(paper["pdf_copies"]) for paper in papers)
    return {
        "schema_version": 1,
        "generator": "scripts/build_literature_catalog.py",
        "deduplication": {
            "primary": "规范化 DOI（去除 DOI URL 前缀并统一大小写）",
            "secondary": "规范化标题（忽略重音、大小写、标点和空白）",
        },
        "counts": {
            "metadata_files": len({source["metadata"] for source in sources}),
            "source_entries": len(sources),
            "unique_papers": len(papers),
            "merged_entries": len(sources) - len(papers),
            "papers_with_pdf": papers_with_pdf,
            "metadata_only": len(papers) - papers_with_pdf,
            "pdf_files": pdf_count,
        },
        "papers": papers,
    }


def escape_bibtex(value):
    """转义 BibTeX 文本中的特殊字符，保留 Unicode 原文。"""
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
    }
    return "".join(replacements.get(character, character) for character in str(value))


def clean_pages(value):
    """把页码范围转成 BibTeX 的双连字符形式。"""
    return re.sub(r"\s*[-–—]\s*", "--", str(value).strip())


def publication_fields(paper):
    """仅从原 venue 中保守提取出版物类型及卷期页字段。"""
    venue = str(paper["venue"]).strip()
    lowered = venue.casefold()
    if "arxiv" in lowered:
        return "misc", {"note": venue}
    is_journal_serial = any(marker in lowered for marker in JOURNAL_SERIALS)
    if not is_journal_serial and any(marker in lowered for marker in CONFERENCE_MARKERS):
        fields = {"booktitle": venue}
        pages_match = re.match(r"^(.*?)(?:,|:)?\s*(?:pp\.?\s*)?(\d+\s*[-–—]\s*\d+)$", venue)
        if pages_match:
            fields["booktitle"] = pages_match.group(1).rstrip(" ,:")
            fields["pages"] = clean_pages(pages_match.group(2))
        return "inproceedings", fields

    fields = {"journal": venue}
    full_match = re.match(
        r"^(.*?)[,\s]+(\d+)(?:\(([^)]+)\))?\s*(?::|,)\s*(.+?)(?:\s*\(\d{4}\))?$",
        venue,
    )
    if full_match:
        fields["journal"] = full_match.group(1).rstrip(" ,")
        fields["volume"] = full_match.group(2)
        if full_match.group(3):
            fields["number"] = full_match.group(3)
        fields["pages"] = clean_pages(full_match.group(4))
    else:
        volume_match = re.match(r"^(.*?)[,\s]+(\d+)(?:\(([^)]+)\))?(?:\s*\(\d{4}\))?$", venue)
        if volume_match:
            fields["journal"] = volume_match.group(1).rstrip(" ,")
            fields["volume"] = volume_match.group(2)
            if volume_match.group(3):
                fields["number"] = volume_match.group(3)
    return "article", fields


def render_bibtex(catalog):
    """生成按稳定 key 排序的 BibTeX 文本。"""
    lines = [
        "% 本文件由 scripts/build_literature_catalog.py 自动生成，请勿手改。",
        "% 规范 DOI、URL、开放获取 URL 和原始 Unicode 题名/作者均予以保留。",
        "",
    ]
    for paper in catalog["papers"]:
        entry_type, fields = publication_fields(paper)
        fields = {
            "author": " and ".join(paper["authors"]),
            "title": paper["title"],
            **fields,
            "year": paper["year"],
        }
        if paper.get("doi"):
            fields["doi"] = paper["doi"]
        if paper.get("url"):
            fields["url"] = paper["url"]
        if paper.get("oa_url"):
            fields["oa_url"] = paper["oa_url"]
        lines.append(f"@{entry_type}{{{paper['id']},")
        for name, value in fields.items():
            if name == "title":
                rendered = "{" + escape_bibtex(value) + "}"
            else:
                rendered = escape_bibtex(value)
            lines.append(f"  {name} = {{{rendered}}},")
        lines.extend(["}", ""])
    return "\n".join(lines)


def render_catalog(catalog):
    """序列化规范目录，确保重复运行字节一致。"""
    header = (
        "# 本文件由 scripts/build_literature_catalog.py 自动生成，请勿手改。\n"
        "# 主题文件允许重复收录；此处的每篇论文仅保留一个规范条目。\n"
    )
    return header + yaml.safe_dump(
        catalog,
        allow_unicode=True,
        sort_keys=False,
        width=100,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=PROJECT, help="项目根目录")
    parser.add_argument("--check", action="store_true", help="只检查现有产物是否可复现，不写文件")
    args = parser.parse_args()
    root = args.root.resolve()
    catalog = build_catalog(root)
    outputs = {
        root / CATALOG_PATH: render_catalog(catalog),
        root / BIB_PATH: render_bibtex(catalog),
    }
    if args.check:
        stale = [
            path for path, content in outputs.items() if not path.is_file() or path.read_text(encoding="utf-8") != content
        ]
        if stale:
            raise SystemExit("以下文献产物需要重新生成：" + ", ".join(str(path) for path in stale))
        print("文献目录与 BibTeX 均可复现，无需更新。")
        return
    for path, content in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    counts = catalog["counts"]
    print(
        f"已生成 {counts['unique_papers']} 篇唯一论文的目录和 BibTeX；"
        f"合并 {counts['merged_entries']} 条重复记录，"
        f"其中 {counts['papers_with_pdf']} 篇有本地 PDF，{counts['metadata_only']} 篇仅元数据。"
    )


if __name__ == "__main__":
    main()
