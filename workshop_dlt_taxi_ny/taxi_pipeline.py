"""dlt pipeline for NYC taxi data from the Data Engineering Zoomcamp REST API."""

import dlt
from dlt.sources.rest_api import rest_api_resources
from dlt.sources.rest_api.typing import RESTAPIConfig


BASE_URL = "https://us-central1-dlthub-analytics.cloudfunctions.net/data_engineering_zoomcamp_api"


@dlt.source
def taxi_pipeline_rest_api_source():
    """Define dlt resources from the NYC taxi REST API (paginated JSON, 1000 records per page). No auth required."""
    config: RESTAPIConfig = {
        "client": {
            "base_url": BASE_URL,
        },
        "resource_defaults": {
            "primary_key": "id",
            "write_disposition": "replace",
            "endpoint": {
                "params": {
                    "limit": 1000,
                },
            },
        },
        "resources": [
            {
                "name": "taxi_rides",
                "endpoint": {
                    "path": "",
                    "method": "GET",
                    "params": {
                        "limit": 1000,
                    },
                    "paginator": {
                        "type": "offset",
                        "limit": 1000,
                        "offset": 0,
                        "limit_param": "limit",
                        "offset_param": "offset",
                        "total_path": None,
                        "stop_after_empty_page": True,
                    },
                },
            },
        ],
    }

    yield from rest_api_resources(config)


pipeline = dlt.pipeline(
    pipeline_name="taxi_pipeline",
    destination="duckdb",
    refresh="drop_sources",
    progress="log",
)


if __name__ == "__main__":
    load_info = pipeline.run(taxi_pipeline_rest_api_source())
    print(load_info)
