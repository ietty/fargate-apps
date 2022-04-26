from asyncio import streams
from aws_cdk import (
    Duration,
    aws_ec2 as ec2,
    aws_elasticloadbalancingv2 as elb,
    aws_s3 as s3,
    aws_ecs as ecs,
    aws_route53 as route53,
    aws_iam as iam,
    aws_route53_targets as r53_targes,
    aws_ecr as ecr,
)

from constructs import Construct


class FargateServiceHostHeader():
    """
    既存のALBにホストヘッダベース振り分けでfargate serviceを追加する。
    """

    # TODO:Constractsになっていないので継承する。
    def __init__(
        self, scope: Construct,
        id: str,
        *,
        task_def: ecs.TaskDefinition,
        cluster: ecs.ICluster,
        vpc_subnets: list[ec2.ISubnet],
        security_groups: list[ec2.ISecurityGroup],
        host_name: str,
        hosted_zone: route53.IHostedZone,
        listener: elb.ApplicationListener,
        alb_priority: int,
        container_name: str,
        container_port: int = 80,
        desired_count: int = 1,
        health_check_path: str = '/',
        ttl=Duration.minutes(30),
    ) -> None:

        service = ecs.FargateService(
            scope, f'{id}-service',
            cluster=cluster,
            task_definition=task_def,
            security_groups=security_groups,
            desired_count=desired_count,
            service_name=f'{id}_service',
            vpc_subnets=vpc_subnets,
        )

        targets = service.load_balancer_target(
            container_name=container_name,
            container_port=container_port,
        )

        # TODO:このやり方だとdestroy時にalbリスナーのルールとalb targetが消えない
        # 当面放置(手動で消すとcdk.outの情報が崩れる)
        # 今後lambdaで自動で消すとか？
        # ref. https://blog.i-tale.jp/2022/01/d1/
        listener.add_targets(
            f'{id}-targets',
            target_group_name=f'staging-ecs-alb-{id}',
            targets=[targets],
            conditions=[
                elb.ListenerCondition.host_headers([host_name])
            ],
            priority=alb_priority,
            health_check=elb.HealthCheck(
                path=health_check_path,
            ),
            port=container_port,
            protocol=elb.ApplicationProtocol.HTTP
        )

        route53.ARecord(
            scope, f'{id}-arecord',
            zone=hosted_zone,
            record_name=host_name,
            ttl=ttl,
            target=route53.RecordTarget.from_alias(
                r53_targes.LoadBalancerTarget(listener.load_balancer)
            )
        )


class FargateHelper():
    def create_task_def(
        self, scope: Construct,
        id: str,
        *,
        image: ecs.RepositoryImage,
        task_role: iam.IRole,
        execution_role: iam.IRole,
        cpu: int = 256,
        memory_limit_mib: int = 512,
        volume: ecs.Volume | None = None,
        port: int,
        mount_points: list[ecs.MountPoint] = None,
        environment: dict = None,
        command: list[str] = None,
    ):
        task_def = ecs.FargateTaskDefinition(
            scope, f'{id}-def',
            cpu=cpu,
            memory_limit_mib=memory_limit_mib,
            execution_role=execution_role,
            task_role=task_role,
            family=f'fargate-{id}-def',
        )
        if volume is not None:
            task_def.add_volume(**volume)
        

        container_def = task_def.add_container(
            f'{id}-container',
            image=image,
            logging=ecs.LogDriver.aws_logs(
                stream_prefix=f'{id}-container'
            ),
            environment=environment,
            command=command,
            linux_parameters=ecs.LinuxParameters(
                scope, f'{id}-param',
                init_process_enabled=True
            )
        )

        portmap = ecs.PortMapping(container_port=port, host_port=port)
        container_def.add_port_mappings(portmap)

        if mount_points is not None and len(mount_points) > 0:
            for point in mount_points:
                container_def.add_mount_points(point)

        return task_def

    def ecr_image(
        self,
        scope: Construct,
        repository_name: str,
        tag,
    ):
        repos = ecr.Repository.from_repository_name(
            scope,
            repository_name,
            repository_name
        )
        image = ecs.ContainerImage.from_ecr_repository(
            repos,
            tag
        )
        return image
