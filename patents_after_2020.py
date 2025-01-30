#!/usr/bin/env python3
"""
Crawl patents from patents.justia.com,
and filter those after 2020.
"""
import patent_crawler

def condition(patent: patent_crawler.Patent) -> bool:
    return patent.file_date.year >= 2020

def main(company: str):
    # Get all patents and filter out those satisfying the condition
    patents = patent_crawler.get_all_patents(company)
    patents_filtered = list(filter(condition, patents))

    # Write the filtered patents to a file
    with open(f"output/{company}_patents_after_2020.txt", "w") as f:
        for idx, patent in enumerate(patents_filtered):
            f.write(f"{idx+1}\t{patent.title}\t{patent.detail_url}\n")
    print(f"Found {len(patents_filtered)} patents by {company} after 2020")

meta = "meta-platforms-inc"
openai = "openai-opco-llc"
main(openai)
