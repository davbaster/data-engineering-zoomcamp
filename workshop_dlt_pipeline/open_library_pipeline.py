"""dlt pipeline to ingest data from the Open Library REST API (books endpoint)."""

import dlt
from dlt.sources.rest_api import rest_api_resources
from dlt.sources.rest_api.typing import RESTAPIConfig


@dlt.source
def open_library_rest_api_source():
    """Define dlt resources from Open Library REST API endpoints.
    Base URL and books endpoint per https://openlibrary.org/dev/docs/api/books.
    No authentication required for public GET /api/books.
    """
    config: RESTAPIConfig = {
        "client": {
            "base_url": "https://openlibrary.org/",
        },
        "resource_defaults": {
            "write_disposition": "replace",
            "endpoint": {
                "params": {
                    "format": "json",
                    "jscmd": "data",
                }
            },
        },
        "resources": [
            {
                "name": "books",
                "endpoint": {
                    "path": "api/books",
                    "method": "GET",
                    "params": {
                        "bibkeys": "ISBN:0451526538,ISBN:0201558025,ISBN:0385472579",
                    },
                    "data_selector": "*",
                    "paginator": {"type": "single_page"},
                },
            },
        ],
    }

    yield from rest_api_resources(config)


pipeline = dlt.pipeline(
    pipeline_name='open_library_pipeline',
    destination='duckdb',
    # `refresh="drop_sources"` ensures the data and the state is cleaned
    # on each `pipeline.run()`; remove the argument once you have a
    # working pipeline.
    refresh="drop_sources",
    # show basic progress of resources extracted, normalized files and load-jobs on stdout
    progress="log",
)


if __name__ == "__main__":
    load_info = pipeline.run(open_library_rest_api_source())
    print(load_info)  # noqa: T201
