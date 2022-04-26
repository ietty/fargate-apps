import importlib
from aws_cdk import (
    Stack,
    aws_ecs as ecs,
)
from constructs import Construct
from lib.alb_stack import AlbStack

import patterns.fargate_patterns as fargate_patterns


class ScipyStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, site: str, alb_stack: AlbStack, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        id = 'scipy'
        image = ecs.ContainerImage.from_registry('jupyter/scipy-notebook')
        port = 8888

        md = importlib.import_module(f'env.{site}')
        rs = md.Resource(self)

        fargate_patterns.FargateHostHeader(
            self, id,
            image=image,
            cluster=rs.cluster,
            security_groups=[rs.sg_all_private],
            vpc_subnets=rs.private_subnets,
            task_role=rs.task_role_default,
            execution_role=rs.execution_role,
            host_name=f'{id}.ietty.info',
            hosted_zone=rs.info_zone,
            listener=alb_stack.listener,
            alb_priority=20,
            port=port,
            cpu=512,
            memory_limit_mib=2048,
            health_check_path='/login',
            ttl=rs.domain_ttl,
        )
