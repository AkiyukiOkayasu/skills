#!/usr/bin/env python3
"""PDF の必要部分だけを抽出または画像化する薄いラッパー。"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Iterator


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="PDF の必要部分だけを抽出または画像化する"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect_parser = subparsers.add_parser(
        "inspect", help="pdfinfo で PDF の基本情報を確認する"
    )
    add_common_input_args(inspect_parser)
    inspect_parser.add_argument(
        "--download-dir",
        type=Path,
        default=None,
        help="URL 入力時の保存先ディレクトリ。省略時は一時ディレクトリを使う",
    )

    extract_parser = subparsers.add_parser(
        "extract", help="opendataloader-pdf で必要ページだけ抽出する"
    )
    add_common_input_args(extract_parser)
    extract_parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("tmp/pdfs"),
        help="出力先ディレクトリ",
    )
    extract_parser.add_argument(
        "--pages",
        default=None,
        help='抽出対象ページ。例: "12-16,19"',
    )
    extract_parser.add_argument(
        "--query",
        action="append",
        default=[],
        help="抽出後に内容を絞り込むキーワード。複数指定可",
    )
    extract_parser.add_argument(
        "--format",
        default="json,markdown",
        help="opendataloader-pdf の出力形式",
    )
    extract_parser.add_argument(
        "--download-dir",
        type=Path,
        default=None,
        help="URL 入力時の保存先ディレクトリ。省略時は output-dir/downloads を使う",
    )
    extract_parser.add_argument(
        "--full-backend",
        action="store_true",
        help="hybrid-mode full を指定する",
    )
    extract_parser.add_argument(
        "--hybrid-url",
        default=None,
        help="hybrid backend URL",
    )
    extract_parser.add_argument(
        "--hybrid-timeout",
        default=None,
        help="hybrid backend timeout(ms)",
    )
    extract_parser.add_argument(
        "--hybrid-fallback",
        action="store_true",
        help="backend 失敗時に Java-only へフォールバックする",
    )
    extract_parser.add_argument(
        "--use-struct-tree",
        action="store_true",
        help="PDF の structure tree を優先利用する",
    )
    extract_parser.add_argument(
        "--table-method",
        default=None,
        choices=("default", "cluster"),
        help="表抽出方式",
    )
    extract_parser.add_argument(
        "--keep-line-breaks",
        action="store_true",
        help="元の改行を保持する",
    )
    extract_parser.add_argument(
        "--include-header-footer",
        action="store_true",
        help="ヘッダ / フッタを保持する",
    )
    extract_parser.add_argument(
        "--to-stdout",
        action="store_true",
        help="フィルタ結果を stdout に JSON で出す",
    )
    extract_parser.add_argument(
        "--quiet",
        action="store_true",
        help="opendataloader-pdf のログを抑制する",
    )

    render_parser = subparsers.add_parser(
        "render", help="回路図や図面のような PDF を PNG に変換する"
    )
    add_common_input_args(render_parser)
    render_parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("tmp/pdfs/rendered"),
        help="PNG 出力先ディレクトリ",
    )
    render_parser.add_argument(
        "--pages",
        default=None,
        help='画像化するページ。例: "2-4,7"',
    )
    render_parser.add_argument(
        "--dpi",
        type=int,
        default=200,
        help="PNG 変換 DPI",
    )
    render_parser.add_argument(
        "--download-dir",
        type=Path,
        default=None,
        help="URL 入力時の保存先ディレクトリ。省略時は output-dir/downloads を使う",
    )

    return parser.parse_args()


def add_common_input_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("input", help="ローカル PDF パスまたは PDF URL")


def is_url(value: str) -> bool:
    parsed = urllib.parse.urlparse(value)
    return parsed.scheme in {"http", "https"}


def resolve_input(input_value: str, download_dir: Path | None) -> tuple[Path, bool]:
    if not is_url(input_value):
        path = Path(input_value).expanduser().resolve()
        if not path.exists():
            raise FileNotFoundError(f"PDF が見つかりません: {path}")
        return path, False

    target_dir = download_dir or Path(tempfile.mkdtemp(prefix="pdf-ingest-"))
    target_dir.mkdir(parents=True, exist_ok=True)
    name = Path(urllib.parse.urlparse(input_value).path).name or "download.pdf"
    if not name.lower().endswith(".pdf"):
        name = f"{name}.pdf"
    target = target_dir / name
    urllib.request.urlretrieve(input_value, target)
    return target.resolve(), True


def run_command(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, check=False, text=True, capture_output=True)


def inspect_pdf(input_value: str, download_dir: Path | None) -> int:
    pdf_path, cleanup = resolve_input(input_value, download_dir)
    try:
        result = run_command(["pdfinfo", str(pdf_path)])
        if result.returncode != 0:
            sys.stderr.write(result.stderr)
            return result.returncode
        print(json.dumps(parse_pdfinfo(result.stdout, pdf_path), ensure_ascii=False, indent=2))
        return 0
    finally:
        cleanup_download(pdf_path, cleanup)


def parse_pdfinfo(text: str, pdf_path: Path) -> dict[str, Any]:
    info: dict[str, Any] = {"file": str(pdf_path)}
    for line in text.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        info[normalize_key(key)] = value.strip()
    return info


def normalize_key(key: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", key.strip().lower()).strip("_")


def extract_pdf(args: argparse.Namespace) -> int:
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    download_dir = args.download_dir or output_dir / "downloads"
    pdf_path, cleanup = resolve_input(args.input, download_dir)
    try:
        cmd = build_opendataloader_command(pdf_path, output_dir, args)
        result = run_command(cmd)
        if result.returncode != 0:
            sys.stderr.write(result.stdout)
            sys.stderr.write(result.stderr)
            return result.returncode
        if not args.quiet and result.stdout.strip():
            sys.stderr.write(result.stdout)

        produced = collect_outputs(pdf_path, output_dir, args.format)
        filtered = filter_results(produced.get("json"), args.query)
        if filtered is not None:
            filtered_path = output_dir / f"{pdf_path.stem}.filtered.json"
            filtered_path.write_text(
                json.dumps(filtered, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            produced["filtered_json"] = filtered_path
            if args.to_stdout:
                print(json.dumps(filtered, ensure_ascii=False, indent=2))
            else:
                print_compact_matches(filtered)

        print_output_summary(produced, args.query, stdout=args.to_stdout)
        return 0
    finally:
        cleanup_download(pdf_path, cleanup)


def render_pdf(args: argparse.Namespace) -> int:
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    download_dir = args.download_dir or output_dir / "downloads"
    pdf_path, cleanup = resolve_input(args.input, download_dir)
    try:
        prefix = output_dir / pdf_path.stem
        cmd = [
            "pdftoppm",
            "-png",
            "-r",
            str(args.dpi),
        ]
        page_ranges = parse_page_ranges(args.pages)
        if page_ranges:
            first_page = min(start for start, _ in page_ranges)
            last_page = max(end for _, end in page_ranges)
            cmd.extend(["-f", str(first_page), "-l", str(last_page)])
        cmd.extend([str(pdf_path), str(prefix)])
        result = run_command(cmd)
        if result.returncode != 0:
            sys.stderr.write(result.stderr)
            return result.returncode

        images = sorted(output_dir.glob(f"{pdf_path.stem}-*.png"))
        images = filter_rendered_images(images, page_ranges)
        print(
            json.dumps(
                {
                    "source": str(pdf_path),
                    "dpi": args.dpi,
                    "pages": args.pages,
                    "images": [str(path) for path in images],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    finally:
        cleanup_download(pdf_path, cleanup)


def build_opendataloader_command(
    pdf_path: Path, output_dir: Path, args: argparse.Namespace
) -> list[str]:
    cmd = [
        "opendataloader-pdf",
        str(pdf_path),
        "-o",
        str(output_dir),
        "-f",
        args.format,
    ]
    if args.pages:
        cmd.extend(["--pages", args.pages])
    cmd.extend(["--hybrid", "docling-fast"])
    if args.full_backend:
        cmd.extend(["--hybrid-mode", "full"])
    if args.hybrid_url:
        cmd.extend(["--hybrid-url", args.hybrid_url])
    if args.hybrid_timeout:
        cmd.extend(["--hybrid-timeout", args.hybrid_timeout])
    if args.hybrid_fallback:
        cmd.append("--hybrid-fallback")
    if args.use_struct_tree:
        cmd.append("--use-struct-tree")
    if args.table_method:
        cmd.extend(["--table-method", args.table_method])
    if args.keep_line_breaks:
        cmd.append("--keep-line-breaks")
    if args.include_header_footer:
        cmd.append("--include-header-footer")
    if args.quiet:
        cmd.append("--quiet")
    return cmd


def collect_outputs(pdf_path: Path, output_dir: Path, formats: str) -> dict[str, Path]:
    produced: dict[str, Path] = {}
    stem = pdf_path.stem
    for fmt in [item.strip() for item in formats.split(",") if item.strip()]:
        suffix = {
            "json": ".json",
            "markdown": ".md",
            "text": ".txt",
            "html": ".html",
            "pdf": ".pdf",
            "tagged-pdf": ".tagged.pdf",
        }.get(fmt)
        if suffix is None:
            continue
        path = output_dir / f"{stem}{suffix}"
        if path.exists():
            produced[fmt] = path
    return produced


def filter_results(json_path: Path | None, queries: list[str]) -> dict[str, Any] | None:
    if json_path is None or not queries:
        return None
    doc = json.loads(json_path.read_text(encoding="utf-8"))
    lowered = [query.casefold() for query in queries]
    matches = []
    for element in iter_elements(doc):
        haystack = " ".join(
            str(element.get(key, ""))
            for key in ("content", "description", "caption", "type")
        ).casefold()
        if all(query in haystack for query in lowered):
            matches.append(
                {
                    "type": element.get("type"),
                    "page": element.get("page number"),
                    "bbox": element.get("bounding box"),
                    "content": element.get("content"),
                    "description": element.get("description"),
                }
            )
    return {
        "source": doc.get("file name") or json_path.name,
        "query": queries,
        "match_count": len(matches),
        "matches": matches,
    }


def iter_elements(node: Any) -> Iterator[dict[str, Any]]:
    if isinstance(node, dict):
        if "type" in node:
            yield node
        kids = node.get("kids")
        if isinstance(kids, list):
            for child in kids:
                yield from iter_elements(child)
        return
    if isinstance(node, list):
        for child in node:
            yield from iter_elements(child)


def parse_page_ranges(pages: str | None) -> list[tuple[int, int]]:
    if not pages:
        return []
    ranges: list[tuple[int, int]] = []
    for part in pages.split(","):
        token = part.strip()
        if not token:
            continue
        if "-" in token:
            start_text, end_text = token.split("-", 1)
            start = int(start_text)
            end = int(end_text)
        else:
            start = int(token)
            end = start
        if start <= 0 or end < start:
            raise ValueError(f"無効なページ範囲です: {token}")
        ranges.append((start, end))
    return ranges


def filter_rendered_images(
    images: list[Path], page_ranges: list[tuple[int, int]]
) -> list[Path]:
    if not page_ranges:
        return images
    allowed_pages = {
        page for start, end in page_ranges for page in range(start, end + 1)
    }
    kept = []
    for image in images:
        match = re.search(r"-(\d+)\.png$", image.name)
        if match and int(match.group(1)) in allowed_pages:
            kept.append(image)
    return kept


def print_compact_matches(filtered: dict[str, Any]) -> None:
    print(
        json.dumps(
            {
                "source": filtered["source"],
                "query": filtered["query"],
                "match_count": filtered["match_count"],
                "matches": filtered["matches"][:20],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def print_output_summary(
    produced: dict[str, Path], queries: list[str], stdout: bool
) -> None:
    if stdout:
        return
    summary = {
        "outputs": {name: str(path) for name, path in produced.items()},
        "filtered": bool(queries),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def cleanup_download(pdf_path: Path, cleanup: bool) -> None:
    if not cleanup:
        return
    parent = pdf_path.parent
    if parent.exists():
        shutil.rmtree(parent, ignore_errors=True)


def main() -> int:
    args = parse_args()
    if args.command == "inspect":
        return inspect_pdf(args.input, args.download_dir)
    if args.command == "extract":
        return extract_pdf(args)
    if args.command == "render":
        return render_pdf(args)
    raise AssertionError(f"unknown command: {args.command}")


if __name__ == "__main__":
    sys.exit(main())
