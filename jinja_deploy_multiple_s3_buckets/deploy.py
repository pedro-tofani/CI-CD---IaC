import boto3
import logging
from botocore.exceptions import ClientError
import jinja2
import yaml
import os


logging.getLogger().setLevel(logging.INFO)
cloudformation_client = boto3.client('cloudformation')


def create_stack(stack_name, template_body):
    """[Function to create the stack in AWS]
    """
    cloudformation_client.create_stack(
        StackName=stack_name,
        TemplateBody=template_body,
        Capabilities=['CAPABILITY_IAM', 'CAPABILITY_NAMED_IAM'],
        TimeoutInMinutes=30,
        OnFailure='ROLLBACK'
    )

    cloudformation_client.get_waiter('stack_create_complete').wait(
        StackName=stack_name,
        WaiterConfig={'Delay': 5, 'MaxAttempts': 600}
    )

    cloudformation_client.get_waiter('stack_exists').wait(StackName=stack_name)
    logging.info(f'CREATE COMPLETE')


def update_stack(stack_name, template_body):
    """[Function to update an existing stack in AWS]

    Exceptions:
        [ClientError]: [If the stack does not needs updates]
    """
    try:
        cloudformation_client.update_stack(
            StackName=stack_name,
            Capabilities=['CAPABILITY_IAM', 'CAPABILITY_NAMED_IAM'],
            TemplateBody=template_body
        )

    except ClientError as e:
        if 'No updates are to be performed' in str(e):
            logging.info(
                f'SKIPPING UPDATE: No updates to be performed at stack {stack_name}')
            return e

    cloudformation_client.get_waiter('stack_update_complete').wait(
        StackName=stack_name,
        WaiterConfig={'Delay': 5, 'MaxAttempts': 600}
    )

    cloudformation_client.get_waiter('stack_exists').wait(StackName=stack_name)
    logging.info(f'UPDATE COMPLETE')


def get_existing_stacks():
    """[Function to obtain existing stacks names in AWS]

    Returns:
        [str]: [List of existing stacks names]
    """
    response = cloudformation_client.list_stacks(
        StackStatusFilter=['CREATE_COMPLETE',
                           'UPDATE_COMPLETE', 'UPDATE_ROLLBACK_COMPLETE']
    )

    return [stack['StackName'] for stack in response['StackSummaries']]


def _get_abs_path(path):
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), path)


def create_or_update_stack():
    """[Function responsible for creating or updating the stack in AWS]
    """
    stack_name = "s3Buckets"
    with open(_get_abs_path('buckets_s3.yaml')) as f:
        template_body = f.read()

    existing_stacks = get_existing_stacks()

    if stack_name in existing_stacks:
        logging.info(f'UPDATING STACK {stack_name}')
        update_stack(stack_name, template_body)
    else:
        logging.info(f'CREATING STACK {stack_name}')
        create_stack(stack_name, template_body)


def render_template():
    """[Function responsible for rendering the template of the IaC]
    """
    logging.info(f'RENDERING JINJA')
    with open(_get_abs_path('buckets_s3.yaml.j2'), 'r') as f:
        buckets_s3_yaml = f.read()

    with open(_get_abs_path('config.yaml'), 'r') as f:
        config = yaml.safe_load(f)

    buckets_s3_template = jinja2.Template(buckets_s3_yaml)
    buckets_s3_rendered = buckets_s3_template.render({**config, **os.environ})

    with open(_get_abs_path('buckets_s3.yaml'), 'w') as f:
        f.write(buckets_s3_rendered)
    logging.info(f'JINJA RENDERED')


if __name__ == '__main__':
    render_template()
    create_or_update_stack()
