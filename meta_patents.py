#!/usr/bin/env python3
"""
Crawl meta patents from patents.justia.com,
and filter those after 2020.
"""
import patent_crawler

def main():
    meta_patents = patent_crawler.get_all_patents("meta-platforms-inc")
    meta_patents = [p for p in meta_patents if p.file_date.year >= 2020]
