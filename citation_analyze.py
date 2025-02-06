#!/usr/bin/env python3
import patent_crawler
from typing import Dict, List, Tuple

from rich import traceback
traceback.install(show_locals=True)
from rich.progress import track
from tqdm import tqdm
import gc

def analyze_citations(company: str) -> Dict[str, int]:
    print("Filtering out patents after 2020")
    patents = list(filter(lambda x: x.file_date.year>=2020, patent_crawler.get_all_patents(company)))
    length = len(patents)
    del patents

    cited_times: Dict[str, int] = {}

    patents = filter(lambda x: x.file_date.year>=2020, patent_crawler.get_all_patents(company))
    for patent in track(patents, total=length, description=company):
        for cite in patent.citations:
            if cite.patent_id not in cited_times:
                cited_times[cite.patent_id] = 1
            else:
                cited_times[cite.patent_id] += 1
    return cited_times

def first_cite_rate(company: str) -> float:
    cited_times = analyze_citations(company)
    if len(cited_times)==0: return 0

    cited_once = len(list(filter(lambda x: x==1, cited_times.values())))
    return cited_once / len(cited_times)

def main():
    meta = "meta-platforms-inc"
    openai = "openai-opco-llc"
    amazon = "amazon-technologies-inc"
    anthropic = "anthropics-technology-limited"

    for company in meta, openai, amazon, anthropic:
    # for company in amazon, anthropic:
        print(f"First cite rate for {company}: {first_cite_rate(company)}")

if __name__ == "__main__":
    main()
