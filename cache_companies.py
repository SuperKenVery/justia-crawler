#!/usr/bin/env python3
import patent_crawler
import sys
from concurrent.futures import ThreadPoolExecutor

from rich import traceback
traceback.install(show_locals=True)
from rich.progress import track

def parallel_cache(company: str):
    print(f"Fetching patents for {company} in recent 5 years")
    patents = patent_crawler.get_all_patents(company)

    def process_patent(patent):
        # print(f"Processing patent #{patent.patent_id}")
        if patent.file_date.year >= 2020:
            _ = patent.citations  # Trigger any citation-fetching logic

    # Spawn threads to handle patents in parallel
    with ThreadPoolExecutor(max_workers=10) as executor:
        executor.map(process_patent, patents)

def cache(company: str):
    print(f"Fetching patents for {company} in recent 5 years")
    patents = list(filter(lambda x: x.file_date.year>=2020, patent_crawler.get_all_patents(company)))
    length = len(patents)
    del patents

    patents = filter(lambda x: x.file_date.year>=2020, patent_crawler.get_all_patents(company))

    for patent in track(patents, total=length):
        if patent.file_date.year >= 2020:
            _ = patent.citations
        del patent

def main():
    meta = "meta-platforms-inc"
    openai = "openai-opco-llc"
    amazon = "amazon-technologies-inc"
    anthropic = "anthropics-technology-limited"

    if len(sys.argv) > 1:
        parallel_cache(sys.argv[1])
    else:
        for company in meta, openai, amazon, anthropic:
            parallel_cache(company)


main()
