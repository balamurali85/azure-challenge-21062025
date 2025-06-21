import logging
import azure.functions as func
import json
from azure.identity import DefaultAzureCredential
from azure.mgmt.network import NetworkManagementClient
from azure.data.tables import TableServiceClient, TableEntity
import os
import uuid

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Processing VNet creation request.")

    try:
        body = req.get_json()
        resource_group = body.get('resource_group')
        location = body.get('location')
        vnet_name = body.get('vnet_name')
        subnets = body.get('subnets')  # List of {"name": str, "prefix": str}

        # Azure credentials and clients
        credential = DefaultAzureCredential()
        subscription_id = os.environ["AZURE_SUBSCRIPTION_ID"]
        network_client = NetworkManagementClient(credential, subscription_id)

        # Create VNet
        address_space = {"address_prefixes": ["10.0.0.0/16"]}
        subnet_configs = [{"name": s['name'], "address_prefix": s['prefix']} for s in subnets]

        async_vnet_creation = network_client.virtual_networks.begin_create_or_update(
            resource_group_name=resource_group,
            virtual_network_name=vnet_name,
            parameters={
                "location": location,
                "address_space": address_space,
                "subnets": subnet_configs
            }
        )
        vnet_result = async_vnet_creation.result()

        # Save results to Azure Table Storage
        connection_string = os.environ["AZURE_TABLE_CONN"]
        table_service = TableServiceClient.from_connection_string(conn_str=connection_string)
        table_client = table_service.get_table_client("vnetresults")

        entity = TableEntity()
        entity["PartitionKey"] = resource_group
        entity["RowKey"] = str(uuid.uuid4())
        entity["VNetName"] = vnet_name
        entity["Location"] = location
        entity["Subnets"] = json.dumps(subnets)

        table_client.create_entity(entity=entity)

        return func.HttpResponse(f"VNet {vnet_name} created successfully", status_code=200)

    except Exception as e:
        logging.error(str(e))
        return func.HttpResponse(f"Error: {str(e)}", status_code=500)
