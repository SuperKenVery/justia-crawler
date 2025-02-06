#!/usr/bin/env python3
"""
A simple crawler and HTML parser for patents.justia.com
For example usage, see the __main__ block at the end of the file.
"""
from lxml import etree
import requests
from requests.adapters import HTTPAdapter, Retry
from functools import cached_property
from typing import Optional, List, Tuple, Iterator, Dict, ClassVar, Iterable
from datetime import datetime, date
from email import header
from pathlib import Path
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor
import gc

from rich import traceback
traceback.install(show_locals=True)
from rich.console import Console
console = Console()

@dataclass
class Patent:
    use_patent_pool: ClassVar[bool] = False
    patent_pool: ClassVar[Dict[str, "Patent"]] = {}

    @staticmethod
    def parse_date(date_str: str) -> date:
        """
        Parses justia-style date strings
        e.g. "October 29, 2021"
        """
        date_str = date_str.strip()
        for fmt in ["%B %d, %Y", "%b %d, %Y"]:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.date()
            except ValueError:
                pass
        raise ValueError("Failed to match to time str")


    @classmethod
    def from_summary(cls, node, session: requests.Session, base_url: str = "https://patents.justia.com") -> "Patent":
        title = node.xpath('.//div[@class="head"]//a/text()')[0]
        patent_id = node.xpath('.//div[@class="head"]//a/@href')[0].split("/")[-1]
        abstract = (node.xpath('.//div[@class="meta"]/div[@class="abstract"]/text()[last()]') or [None])[0]
        file_date = cls.parse_date(node.xpath('.//div[@class="meta"]/div[@class="date-filed"]/text()[last()]')[0])
        issued_date = cls.parse_date(node.xpath('.//div[@class="meta"]/div[@class="date-issued"]/text()[last()]')[0])
        assignees_matched = node.xpath('.//div[@class="meta"]/div[@class="assignees"]/text()[last()]')
        assignees = assignees_matched[0].strip() if assignees_matched else None

        if cls.use_patent_pool and patent_id in cls.patent_pool:
            return cls.patent_pool[patent_id]

        result = cls(
            title=title,
            patent_id=patent_id,
            abstract=abstract,
            file_date=file_date,
            issued_date=issued_date,
            assignees=assignees,
            session=session,
            _detail_page=None
        )
        if cls.use_patent_pool: cls.patent_pool[patent_id] = result

        return result

    @classmethod
    def from_patent_id(cls, patent_id: str, session: requests.Session) -> "Optional[Patent]":
        if cls.use_patent_pool and patent_id in cls.patent_pool:
            return cls.patent_pool[patent_id]

        page_str = get_patent_detail(patent_id, session)
        if page_str is None: return None

        page = etree.HTML(page_str)
        title = (page.xpath('//h1[@class="heading-1"]//text()') + [""])[0]
        abstract = (page.xpath('//div[@id="abstract"]/p/text()') + [None])[0]
        file_date_matched = page.xpath('//div[@id="history"]//strong[text()="Filed"]/following-sibling::text()[1]')
        file_date = cls.parse_date(file_date_matched[0][2:] if len(file_date_matched)>0 else "Jan 1, 1997")
        issued_date = cls.parse_date(
            (
                page.xpath('//div[@id="history"]//strong[text()="Date of Patent"]/following-sibling::text()[1]') +
                page.xpath('//div[@id="history"]//strong[text()="Publication Date"]/following-sibling::text()[1]') +
                [": Jan 1, 1997"]
            )[0][2:]
        )
        assignees_matched = page.xpath('//div[@id="history"]//strong[text()="Assignee"]/following-sibling::a[1]/text()')
        assignees = assignees_matched[0].strip() if assignees_matched else None

        result = cls(
            title=title,
            patent_id=patent_id,
            abstract=abstract,
            file_date=file_date,
            issued_date=issued_date,
            assignees=assignees,
            session=session,
            _detail_page=page_str
        )
        if cls.use_patent_pool: cls.patent_pool[patent_id] = result

        return result

    title: str
    patent_id: str
    abstract: Optional[str]
    file_date: date
    issued_date: date
    assignees: Optional[str]
    session: requests.Session
    _detail_page: Optional[str]

    @property
    def detail_page(self) -> Optional[str]:
        if self._detail_page is None:
            self._detail_page = get_patent_detail(self.patent_id, self.session)

        return self._detail_page

    @property
    def citations(self) -> Iterable["Patent"]:
        if self.detail_page is None: return []

        page = etree.HTML(self.detail_page)
        patent_ids: List[str] = page.xpath('//div[@id="citations"]//tr/td[1]/a[1]/text()')

        def fetch_patent(id):
            return Patent.from_patent_id(id, session=self.session)

        with ThreadPoolExecutor(max_workers=80) as executor:
            result: List[Optional[Patent]] = list(executor.map(fetch_patent, patent_ids))

        result_nonone: List[Patent] = [x for x in result if x is not None]
        return result_nonone

        # for patent_id in patent_ids:
        #     yield Patent.from_patent_id(patent_id, session=self.session)

    def __rich_repr__(self):
        yield self.title
        yield "Patent ID", self.patent_id
        yield "Abstract", self.abstract

def get_page_content(company: str, page: int, session) -> str:
    url = f"https://patents.justia.com/assignee/{company}?page={page}"

    cache = Path(f"cache/company_{company}_{page}.html")
    cache.parent.mkdir(parents=True, exist_ok=True)
    if cache.exists():
        return cache.read_text()

    # with console.status(f"Fetching page {page}..."):
    print(f"Fetching page {page}...")
    response = session.get(url)

    assert response.status_code==200, f"Failed to get patents from {url}"
    cache.write_text(response.text)

    return response.text

def get_patent_detail(id: str, session) -> Optional[str]:
    url = f"https://patents.justia.com/patent/{id}"

    cache = Path(f"cache/detail_{id}.html")
    cache.parent.mkdir(parents=True, exist_ok=True)
    if cache.exists():
        return cache.read_text()

    # with console.status(f"Fetching patent #{id}..."):
    print(f"Fetching patent #{id}...")
    response = session.get(url)

    if response.status_code!=200: return None

    cache.write_text(response.text)
    return response.text

def get_default_session() -> requests.Session:
    session = requests.Session()
    session.headers["User-Agent"] = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:134.0) Gecko/20100101 Firefox/134.0"

    retries = Retry(total=5, backoff_factor=0.1, status_forcelist=[ 500, 502, 503, 504 ])
    session.mount('http://', HTTPAdapter(max_retries=retries))
    session.mount('https://', HTTPAdapter(max_retries=retries))

    return session

def get_all_patents(company: str, session=get_default_session()) -> Iterator[Patent]:

    page = 1
    base_url = "https://patents.justia.com"

    while True:
        tree = etree.HTML(get_page_content(company, page, session))
        patent_nodes = tree.xpath('//li[@class="has-padding-content-block-30 -zb"]')

        patents = [Patent.from_summary(node, session=session, base_url=base_url) for node in patent_nodes]
        # yield from patents

        while len(patents) > 0:
            yield patents.pop()

        next_btn = tree.xpath('//span[@class="pagination page"]/a[text()="next"]')
        if len(next_btn) > 0:
            page += 1
        else:
            break



if __name__=='__main__':
    from rich import print

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
        print(patent)
        print("===========")
