import importlib
from aws_cdk import (
    Stack,
    aws_ecs as ecs,
    aws_ecr as ecr,
)
from constructs import Construct

from lib.alb_stack import AlbStack
import env.staging as resource_type
import patterns.fargate_patterns as fp


class JupyterStack(Stack):
    """
    JupyterHubを構築する
    Albがdeploy済みであること。
    """

    def __init__(self, scope: Construct, construct_id: str, site: str, alb_stack: AlbStack, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # 既存リソース情報の呼び出し
        md = importlib.import_module(f'env.{site}')
        rs: resource_type.Resource = md.Resource(self)
        helper = fp.FargateHelper()

        # jupyterhubの起動
        id = 'jupyter'
        image = helper.ecr_image(self, 'jupyterhub', '2022042001')

        port = 8000
        #TODO: secretは埋め込む
        env = {
            'HOSTED_DOMAIN': 'ietty.co.jp',
            'OAUTH_CLIENT_ID': '1079595221867-rmalm0buebci983td30nloa029vapn95.apps.googleusercontent.com',
            'OAUTH_CLIENT_SECRET': '4JbvXLwK_MJL_34jz9PR3PNV',
            'OAUTH_CALLBACK_URL': 'https://jupyter.ietty.info/hub/oauth_callback',
        }
        mount_points = [ecs.MountPoint(
            container_path='/mnt',
            source_volume=rs.efs_volume['name'],
            read_only=False,
        )]

        task_def = helper.create_task_def(
            self,
            id,
            image=image,
            execution_role=rs.execution_role,
            task_role=rs.task_role_default,
            cpu=256,
            memory_limit_mib=512,
            volume=rs.efs_volume,
            port=port,
            mount_points=mount_points,
            environment=env,
            command=["jupyterhub", "-f", "/mnt/jupyterhub_config.py"],
        )

        fp.FargateServiceHostHeader(
            self, id,
            task_def=task_def,
            cluster=rs.cluster,
            vpc_subnets=rs.private_subnets,
            security_groups=[rs.sg_all_private],
            host_name=f'{id}.ietty.info',
            hosted_zone=rs.info_zone,
            listener=alb_stack.listener,
            container_name=f'{id}-container',
            container_port=port,
            alb_priority=30,
            health_check_path='/_chp_healthz',
            ttl=rs.domain_ttl,
        )
