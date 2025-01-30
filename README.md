# Justia Crawler

Gets patent data from justia.

## Features
- Crawl all patents of a company from justia
- Cache all fetched HTMLs so you can easily debug without being banned
- Lazily load each single page
- Lazily load each property with cache

## Setup

I'm too lazy to upload this thing to pypi, so you'll have to clone the sources and develop in this folder. Therefore, this is essentially a "development" setup.

We use `pixi` to manage the python environment, which creates a reproducible environment with locked package versions.

To install dependencies,

```bash
# Ensure you have `pixi` installed
pixi install
```

then you could run the example with:
```bash
pixi run python patent_crawler.py
```

## Usage
The bottom of `patent_crawler.py` contains a simple example. `patents_after_2020.py` is also a reference too.

```python3
import patent_crawler
patents = patent_crawler.get_all_patents("meta-platforms-inc")
for p in patents:
    print(p.title)
    print(p.abstract)
    # See more properties in source code
```
