from aws_cdk import (
    aws_s3 as s3,
    Stack
)
from constructs import Construct


class S3Stack(Stack):

    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
        s3.Bucket(self, 'phtf-s3-cdk', bucket_name='phtf-s3-cdk')
