import dlt
from dlt.sources.rest_api import rest_api_resources
from dlt.sources.rest_api.typing import RESTAPIConfig
from dlt.sources.helpers.rest_client.paginators import PageNumberPaginator

BASE_URL = "https://us-central1-dlthub-analytics.cloudfunctions.net/data_engineering_zoomcamp_api"


@dlt.source
def taxi_rest_api_source():
    config: RESTAPIConfig = {
        "client": {
            "base_url": BASE_URL,
        },
        "resource_defaults": {
            "write_disposition": "replace",
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
                    "paginator": PageNumberPaginator(
                        base_page=1,
                        page=1,
                        page_param="page",
                        stop_after_empty_page=True,
                        total_path=None,
                    ),
                },
            },
        ],
    }

    yield from rest_api_resources(config)


pipeline = dlt.pipeline(
    pipeline_name="taxi_pipeline",
    destination="duckdb",
    dataset_name="taxi_data",
    refresh="drop_sources",
    progress="log",
)


if __name__ == "__main__":
    load_info = pipeline.run(taxi_rest_api_source())
    print(load_info)
