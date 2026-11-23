"""验证全局文献目录、主题交叉引用、PDF 和 BibTeX 的一致性。"""

import hashlib
import re
import unittest
from pathlib import Path

import yaml

from scripts.build_literature_catalog import (
    build_catalog,
    escape_bibtex,
    normalize_doi,
    normalize_title,
    render_bibtex,
    render_catalog,
)

PROJECT = Path(__file__).resolve().parents[1]
LITERATURE = PROJECT / "reference/literature"


class LiteratureCatalogTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog_text = (LITERATURE / "catalog.yaml").read_text(encoding="utf-8")
        cls.catalog = yaml.safe_load(cls.catalog_text)
        cls.papers = cls.catalog["papers"]
        cls.bibtex = (LITERATURE / "hazardcast.bib").read_text(encoding="utf-8")
        cls.sources = {}
        cls.topic_sizes = {}
        for path in sorted((LITERATURE / "metadata").glob("*.yaml")):
            document = yaml.safe_load(path.read_text(encoding="utf-8"))
            cls.topic_sizes[document["topic"]] = len(document["papers"])
            for paper in document["papers"]:
                key = (document["topic"], paper["id"])
                cls.sources[key] = paper

    def test_thirteen_topics_have_ten_entries_each(self):
        """输入应完整覆盖 13 个主题及其每类 10 条记录。"""
        self.assertEqual(len(self.topic_sizes), 13)
        self.assertEqual(set(self.topic_sizes.values()), {10})
        self.assertEqual(len(self.sources), 130)

    def test_counts_match_sources_and_expected_range(self):
        """规范论文总数应合理，汇总计数应由实际记录推导。"""
        counts = self.catalog["counts"]
        self.assertGreaterEqual(len(self.papers), 100)
        self.assertLessEqual(len(self.papers), 150)
        self.assertEqual(counts["metadata_files"], len(self.topic_sizes))
        self.assertEqual(counts["source_entries"], len(self.sources))
        self.assertEqual(counts["unique_papers"], len(self.papers))
        self.assertEqual(counts["merged_entries"], len(self.sources) - len(self.papers))
        with_pdf = sum(bool(paper["pdf_copies"]) for paper in self.papers)
        pdf_files = {copy["path"] for paper in self.papers for copy in paper["pdf_copies"]}
        self.assertEqual(counts["papers_with_pdf"], with_pdf)
        self.assertEqual(counts["metadata_only"], len(self.papers) - with_pdf)
        self.assertEqual(counts["pdf_files"], len(pdf_files))

    def test_normalized_doi_and_title_are_unique(self):
        """规范 DOI 和规范标题都不能在总目录重复。"""
        dois = [normalize_doi(paper["doi"]) for paper in self.papers if paper.get("doi")]
        titles = [normalize_title(paper["title"]) for paper in self.papers]
        self.assertEqual(len(dois), len(set(dois)))
        self.assertEqual(len(titles), len(set(titles)))
        self.assertTrue(all(titles))
        for paper in self.papers:
            if paper.get("doi"):
                self.assertEqual(paper["doi"], normalize_doi(paper["doi"]))

    def test_every_source_reference_is_valid_and_complete(self):
        """每条主题记录必须恰好回指一次，并保留原始 ID 和文件路径。"""
        references = {}
        for paper in self.papers:
            self.assertEqual(
                paper["topics"],
                sorted({source["topic"] for source in paper["sources"]}),
            )
            for source in paper["sources"]:
                key = (source["topic"], source["id"])
                self.assertNotIn(key, references)
                references[key] = paper["id"]
                self.assertIn(key, self.sources)
                original = self.sources[key]
                self.assertEqual(
                    source["metadata"],
                    f"reference/literature/metadata/{source['topic']}.yaml",
                )
                self.assertEqual(
                    source["topic_file"],
                    f"reference/literature/topics/{source['topic']}.md",
                )
                self.assertTrue((PROJECT / source["metadata"]).is_file())
                self.assertTrue((PROJECT / source["topic_file"]).is_file())
                for field in ("doi", "url", "oa_url", "pdf_path", "sha256"):
                    self.assertEqual(source[field], original.get(field), (key, field))
        self.assertEqual(set(references), set(self.sources))
        self.assertEqual(len(references), len(self.sources))

    def test_topic_reviews_contain_all_source_ids(self):
        """主题综述中的条目 ID 应与各自原始元数据保持同步。"""
        for topic, source_id in self.sources:
            with self.subTest(topic=topic, source_id=source_id):
                review = LITERATURE / "topics" / f"{topic}.md"
                self.assertIn(source_id, review.read_text(encoding="utf-8"))

    def test_local_markdown_links_resolve(self):
        """总索引、综合综述和主题综述的本地链接必须存在。"""
        documents = [
            PROJECT / "README.md",
            PROJECT / "docs/2026-11-23-literature-review.md",
            LITERATURE / "README.md",
            *sorted((LITERATURE / "topics").glob("*.md")),
        ]
        for document in documents:
            text = document.read_text(encoding="utf-8")
            for target in re.findall(r"(?<!!)\[[^]]+\]\(([^)]+)\)", text):
                if target.startswith(("http://", "https://", "mailto:", "#")):
                    continue
                local_target = target.split("#", 1)[0]
                with self.subTest(document=document.relative_to(PROJECT), target=target):
                    self.assertTrue((document.parent / local_target).resolve().exists())

    def test_all_pdf_copies_exist_and_match_sha256(self):
        """无 PDF 的全新克隆跳过；有部分 PDF 时严格检查全部副本。"""
        declared_paths = [
            PROJECT / copy["path"] for paper in self.papers for copy in paper["pdf_copies"]
        ]
        if not any(path.is_file() for path in declared_paths):
            self.skipTest("工作区没有任何本地 PDF；PDF 内容校验仅在至少有一份副本时启用")
        seen = {}
        for paper in self.papers:
            copies = paper["pdf_copies"]
            if not copies:
                self.assertEqual(paper["access"], "metadata-only")
                self.assertIsNone(paper["pdf_path"])
                self.assertIsNone(paper["sha256"])
                continue
            self.assertIn(paper["pdf_path"], {copy["path"] for copy in copies})
            for copy in copies:
                path = PROJECT / copy["path"]
                self.assertTrue(path.is_file(), path)
                self.assertRegex(copy["sha256"], r"^[0-9a-f]{64}$")
                digest = hashlib.sha256()
                with path.open("rb") as stream:
                    for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                        digest.update(chunk)
                self.assertEqual(digest.hexdigest(), copy["sha256"], copy["path"])
                if copy["path"] in seen:
                    self.assertEqual(seen[copy["path"]], copy["sha256"])
                seen[copy["path"]] = copy["sha256"]
        self.assertEqual(len(seen), self.catalog["counts"]["pdf_files"])

    def test_bibtex_keys_are_unique_and_match_catalog(self):
        """每篇规范论文应恰有一个同 ID 的 BibTeX 条目。"""
        entries = {
            match.group(2): (match.group(1), match.group(3))
            for match in re.finditer(r"(?ms)^@(\w+)\{([^,]+),\n(.*?)^\}", self.bibtex)
        }
        keys = re.findall(r"(?m)^@\w+\{([^,]+),", self.bibtex)
        self.assertEqual(len(keys), len(self.papers))
        self.assertEqual(len(keys), len(set(keys)))
        self.assertEqual(set(keys), {paper["id"] for paper in self.papers})
        self.assertEqual(entries["mardani2025residual"][0], "article")
        self.assertEqual(entries["stengel2020adversarial"][0], "article")
        self.assertEqual(entries["chen2018neural"][0], "inproceedings")
        self.assertEqual(entries["brenowitz2025climate"][0], "misc")
        for paper in self.papers:
            entry_type, body = entries[paper["id"]]
            self.assertIn(entry_type, {"article", "inproceedings", "misc"})
            self.assertIn(escape_bibtex(paper["title"]), body)
            if paper.get("doi"):
                self.assertIn(f"doi = {{{escape_bibtex(paper['doi'])}}}", body)
            if paper.get("url"):
                self.assertIn(f"url = {{{escape_bibtex(paper['url'])}}}", body)
            if paper.get("oa_url"):
                self.assertIn(f"oa_url = {{{escape_bibtex(paper['oa_url'])}}}", body)

    def test_generated_outputs_are_reproducible(self):
        """从主题原件重建的 YAML 和 BibTeX 必须与交付文件逐字一致。"""
        rebuilt = build_catalog(PROJECT)
        self.assertEqual(rebuilt, self.catalog)
        self.assertEqual(render_catalog(rebuilt), self.catalog_text)
        self.assertEqual(render_bibtex(rebuilt), self.bibtex)


if __name__ == "__main__":
    unittest.main()
