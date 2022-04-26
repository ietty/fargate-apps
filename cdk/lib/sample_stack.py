import importlib
from aws_cdk import (
    Duration,
    Stack,
    aws_elasticloadbalancingv2 as elb,
    aws_ecs as ecs,
    aws_route53 as route53,
    aws_route53_targets as r53_targes,
)
from constructs import Construct
from lib.alb_stack import AlbStack


class NginxStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, site: str, alb_stack: AlbStack, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        md = importlib.import_module(f'env.{site}')
        rs = md.Resource(self)

        task_def = ecs.FargateTaskDefinition(
            self, 'nginx-def',
            cpu=256,
            execution_role=rs.execution_role,
            task_role=rs.task_role_default,
            family="sample-nginx",
        )
        task_def.add_container(
            'nginx-container',
            image=ecs.ContainerImage.from_registry('nginx'),
            logging=ecs.LogDriver.aws_logs(
                stream_prefix='nginx-container'
            ),
        ).add_port_mappings(ecs.PortMapping(
            container_port=80, host_port=80
        ))

        service = ecs.FargateService(
            self, 'nginx_sample_service',
            cluster=rs.cluster,
            task_definition=task_def,
            security_groups=[rs.sg_all_private],
            desired_count=4,
            service_name='ngix_sample',
            vpc_subnets=rs.private_subnets
        )

        targets = service.load_balancer_target(
            container_name='nginx-container',
            container_port=80,
        )

        alb_stack.listener.add_targets(
            "nginx-targets",
            target_group_name='staging-ecs-alb-nginx',
            targets=[targets],
            conditions=[
                elb.ListenerCondition.host_headers(["sample.ietty.info"])
            ],
            priority=10,
            health_check=elb.HealthCheck(
                healthy_threshold_count=5,
                unhealthy_threshold_count=5,
                interval=Duration.seconds(5),
                timeout=Duration.seconds(4),
            ),
            port=80,
        )

        route53.ARecord(
            self, 'sample.ietty.info',
            zone=rs.info_zone,
            record_name='sample.ietty.info',
            target=route53.RecordTarget.from_alias(
                r53_targes.LoadBalancerTarget(alb_stack.listener.load_balancer)
            )
        )
