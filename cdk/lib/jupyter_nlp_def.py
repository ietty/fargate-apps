import importlib
from aws_cdk import (
    Stack,
    aws_ecs as ecs,
)
from constructs import Construct

import env.staging as resource_type
import patterns.fargate_patterns as fp

class JupyterNlpDefStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, site: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # 既存リソース情報の呼び出し
        md = importlib.import_module(f'env.{site}')
        rs: resource_type.Resource = md.Resource(self)
        helper = fp.FargateHelper()

        mount_points = [ecs.MountPoint(
            container_path='/mnt',
            source_volume=rs.efs_volume['name'],
            read_only=False,
        )]

        # spawner用のtaskDefを定義
        id = 'nlp'
        image = helper.ecr_image(self, 'nlp', '2022042101')

        task_def = helper.create_task_def(
            self,
            id,
            image=image,
            execution_role=rs.execution_role,
            task_role=rs.task_role_default,
            cpu=512,
            memory_limit_mib=1024,
            volume=rs.efs_volume,
            port=8888,
            mount_points=mount_points,
        )

        self.task_def = task_def
