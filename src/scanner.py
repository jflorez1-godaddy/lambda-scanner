import boto3
import botocore
import logging
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configure logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

DEPRECATED_RUNTIMES = ['python3.6', 'python3.7', 'python3.8']
lambda_client = boto3.client('lambda')
cloudformation_client = boto3.client('cloudformation')

def get_all_lambda_functions() -> List[Dict[str, Any]]:
    """Fetch all Lambda functions."""
    logger.info("Getting all Lambda functions")
    lambdas = []
    try:
        response = lambda_client.list_functions()
        lambdas.extend(response['Functions'])
        while 'NextMarker' in response:
            response = lambda_client.list_functions(Marker=response['NextMarker'])
            lambdas.extend(response['Functions'])
    except botocore.exceptions.BotoCoreError as e:
        logger.error(f"Error fetching Lambda functions: {e}")
    return lambdas

def filter_deprecated_lambda_functions(lambdas: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filter Lambda functions with deprecated runtimes."""
    logger.info("Filtering Lambda functions")
    return [
        lambda_function for lambda_function in lambdas
        if lambda_function.get('Runtime') in DEPRECATED_RUNTIMES and
           lambda_function.get('FunctionName').startswith('SC')
    ]

def fetch_lambda_tags(lambda_function: Dict[str, Any]) -> Dict[str, Any]:
    """Fetch tags for a given Lambda function."""
    try:
        tags = lambda_client.list_tags(Resource=lambda_function['FunctionArn'])['Tags']
        provisioned_product_arn = tags.get('aws:servicecatalog:provisionedProductArn', None)
        sc_resource_physical_id = provisioned_product_arn.split('/')[-1] if provisioned_product_arn else None
        return {
            'FunctionName': lambda_function['FunctionName'],
            'sc_stack_name': tags.get('aws:cloudformation:stack-name', None),
            'sc_stack_id': tags.get('aws:cloudformation:stack-id', None),
            'logical_id': tags.get('aws:cloudformation:logical-id', None),
            'stack_physical_id': sc_resource_physical_id if sc_resource_physical_id else "No SC stack found in tags",
            'parent_stack': "No parent stack found"
        }
    except botocore.exceptions.BotoCoreError as e:
        logger.error(f"Error fetching tags for {lambda_function['FunctionName']}: {e}")
        return {}

def get_lambda_metadata() -> Dict[str, Dict[str, Any]]:
    """Get metadata for all filtered Lambda functions."""
    logger.info("Getting Lambda metadata")
    lambda_metadata = {}
    lambdas = filter_deprecated_lambda_functions(get_all_lambda_functions())
    if not lambdas:
        print(f"No lambdas found with runtimes {DEPRECATED_RUNTIMES}")
        return lambda_metadata
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_lambda = {executor.submit(fetch_lambda_tags, lambda_function): lambda_function for lambda_function in lambdas}
        for future in as_completed(future_to_lambda):
            lambda_function = future_to_lambda[future]
            try:
                data = future.result()
                if data:
                    lambda_metadata[lambda_function['FunctionName']] = data
            except Exception as e:
                logger.error(f"Error processing {lambda_function['FunctionName']}: {e}")
    return lambda_metadata

def update_parent_stack_in_metadata(lambda_mapping_data: Dict[str, Dict[str, Any]]) -> None:
    """Update the parent stack information in the metadata."""
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_stack = {
            executor.submit(cloudformation_client.describe_stack_resources, PhysicalResourceId=metadata["stack_physical_id"]): (lambda_function, metadata)
            for lambda_function, metadata in lambda_mapping_data.items() if metadata["stack_physical_id"]
        }
        for future in as_completed(future_to_stack):
            lambda_function, metadata = future_to_stack[future]
            try:
                response = future.result()
                parent_stack_name = response['StackResources'][0]['StackName']
                lambda_mapping_data[lambda_function]["parent_stack"] = parent_stack_name
            except botocore.exceptions.ClientError as e:
                if e.response['Error']['Code'] == 'ValidationError':
                    logger.warning(f"Stack {metadata['stack_physical_id']} not found")
                else:
                    logger.error(f"Error describing stack resources for {metadata['stack_physical_id']}: {e}")

def print_lambda_stack_information(lambda_mapping_data: Dict[str, Dict[str, Any]]) -> None:
    """Print the Lambda stack information."""
    str_format = "{:<70} {:<40} {:<40}"
    if lambda_mapping_data:
        print(str_format.format('Function Name', 'Stack Name', 'Parent Stack'))
        for lambda_function, metadata in lambda_mapping_data.items():
            print(str_format.format(lambda_function, metadata['sc_stack_name'], metadata['parent_stack']))

def main() -> None:
    """Main function to execute the script."""
    lambda_mapping_data = get_lambda_metadata()
    update_parent_stack_in_metadata(lambda_mapping_data)
    print_lambda_stack_information(lambda_mapping_data)

if __name__ == '__main__':
    main()