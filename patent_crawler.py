#!/usr/bin/env python3
"""
A simple crawler and HTML parser for patents.justia.com
For example usage, see the __main__ block at the end of the file.
"""
from lxml import etree
import requests
from functools import cached_property
from typing import Optional, List, Tuple, Iterator
from datetime import datetime, date
from email import header
from rich import traceback
traceback.install(show_locals=True)
from rich.console import Console
console = Console()
from pathlib import Path

class Patent:
    def __init__(self, node, base_url = "", session=requests.Session()):
        self.node = node
        self.session = session
        self.base_url = base_url    # Used in detail_url, don't include trailing slash

    @property
    def title(self) -> str:
        return self.node.xpath('.//div[@class="head"]//a/text()')[0]

    @cached_property
    def detail_url(self) -> str:
        href = self.node.xpath('.//div[@class="head"]//a/@href')[0]
        # e.g. href = "/patent/12039383"
        return self.base_url + href

    @cached_property
    def abstract(self) -> Optional[str]:
        abstracts = self.node.xpath('.//div[@class="meta"]/div[@class="abstract"]/text()[last()]')
        return abstracts[0] if len(abstracts)>0 else None

    @staticmethod
    def parse_date(date_str: str) -> date:
        """
        Parses justia-style date strings
        e.g. "October 29, 2021"
        """
        date_str = date_str.strip()
        dt = datetime.strptime(date_str, "%B %d, %Y")
        return dt.date()

    @cached_property
    def file_date(self) -> date:
        date_str =  self.node.xpath('.//div[@class="meta"]/div[@class="date-filed"]/text()[last()]')[0]
        return self.parse_date(date_str)


    @cached_property
    def issued_date(self) -> date:
        date_str =  self.node.xpath('.//div[@class="meta"]/div[@class="date-issued"]/text()[last()]')[0]
        return self.parse_date(date_str)


    @cached_property
    def assignees(self) -> str:
        assignee = self.node.xpath('.//div[@class="meta"]/div[@class="assignees"]/text()[last()]')[0]
        return assignee.strip()

    @property
    def owner(self) -> str:
        return self.assignees

def get_page_content(company: str, page: int, session) -> str:
    url = f"https://patents.justia.com/assignee/{company}?page={page}"

    cache = Path(f"cache/{company}_{page}.html")
    cache.parent.mkdir(parents=True, exist_ok=True)
    if cache.exists():
        return cache.read_text()

    with console.status(f"Fetching page {page}..."):
        response = session.get(url)

    assert response.status_code==200, f"Failed to get patents from {url}"
    cache.write_text(response.text)

    return response.text

def get_all_patents(company: str, session=None) -> Iterator[Patent]:
    if not session:
        session = requests.Session()
        session.headers["User-Agent"] = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:134.0) Gecko/20100101 Firefox/134.0"
    # assert session is not None
    page = 1
    base_url = "https://patents.justia.com"

    while True:
        tree = etree.HTML(get_page_content(company, page, session))
        patent_nodes = tree.xpath('//li[@class="has-padding-content-block-30 -zb"]')
        patents = [Patent(node, base_url=base_url, session=session) for node in patent_nodes]
        # import pdb; pdb.set_trace()
        yield from patents

        next_btn = tree.xpath('//span[@class="pagination page"]/a[text()="next"]')
        if len(next_btn) > 0:
            page += 1
        else:
            break

if __name__=='__main__':
    print("Trying to get patents from Meta...")

    # To get the "meta-platforms-inc" text:
    # 1. Google "find patents by meta"
    # 2. Goto "Patents Assigned to Meta Platforms, Inc." from justia
    # 3. Your browser URL would be https://patents.justia.com/assignee/meta-platforms-inc
    # 4. The last part of the URL is what you need
    patents = get_all_patents("meta-platforms-inc")

    # Now you got an iterator, you could iterate it or convert
    # it to a list, but you cannot index it like patents[2]
    for patent in patents:
        print(patent.title)
        print(patent.detail_url)
        print(patent.abstract)
        print(patent.file_date)
        print(patent.issued_date)
        print(patent.owner)
        print("===========")
