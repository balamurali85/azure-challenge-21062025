import azure.functions as func
from azure.data.tables import TableServiceClient
import os
import json

def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        connection_string = os.environ["AZURE_TABLE_CONN"]
        table_service = TableServiceClient.from_connection_string(conn_str=connection_string)
        table_client = table_service.get_table_client("vnetresults")

        entities = table_client.list_entities()
        results = [entity for entity in entities]

        return func.HttpResponse(json.dumps(results), status_code=200, mimetype="application/json")
    except Exception as e:
        return func.HttpResponse(str(e), status_code=500)
