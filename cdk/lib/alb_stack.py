import importlib
from aws_cdk import (
    Duration,
    Stack,
    aws_elasticloadbalancingv2 as elb,
)
from constructs import Construct


class AlbStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, site: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        md = importlib.import_module(f'env.{site}')
        rs = md.Resource(self)

        # 先にデフォルトのダミーターゲットグループを作成しておく
        tg = elb.ApplicationTargetGroup(
            self, f'{site}-ecs-default',
            target_group_name=f'{site}-ecs-default',
            port=9999,
            protocol=elb.ApplicationProtocol.HTTP,
            vpc=rs.vpc,
            target_type=elb.TargetType.IP,
            health_check=elb.HealthCheck(
                healthy_threshold_count=5,
                unhealthy_threshold_count=5,
                interval=Duration.seconds(5),
                timeout=Duration.seconds(4),
            )
        )

        # albの作成
        alb = elb.ApplicationLoadBalancer(
            self, f'{site}-ecs-alb',
            security_group=rs.sg_alb,
            vpc=rs.vpc,
            load_balancer_name=f'{site}-ecs-alb',
            internet_facing=True,
            vpc_subnets=rs.public_subnets,
        )
        alb.log_access_logs(rs.elb_log_bucket, f'{site}-ecs-alb')

        # httpsリスナーの作成
        listener = alb.add_listener(
            'listener',
            certificates=[rs.alb_certs],
            default_target_groups=[tg],
            open=False,
            port=443,
        )

        self.listener = listener
