from aws_cdk import (
    Duration,
    Stack,
    aws_ec2 as ec2,
    aws_elasticloadbalancingv2 as elb,
    aws_s3 as s3,
    aws_ecs as ecs,
    aws_route53 as route53,
    aws_iam as iam,
    aws_route53_targets as r53_targes,
)


class Resource():
    """vpc別の既存リソース参照"""

    def __init__(self, stack):

        self.vpc = ec2.Vpc.from_lookup(
            stack, "staging-vpc",
            region='ap-northeast-1',
            vpc_id='vpc-1aa4e07f'
        )

        self.sg_alb = ec2.SecurityGroup.from_lookup_by_name(
            stack, 'staging-http-public',
            security_group_name='staging-http-public',
            vpc=self.vpc
        )

        self.sg_all_private = ec2.SecurityGroup.from_lookup_by_name(
            stack, 'staging-all-private',
            security_group_name='staging-all-privte',
            vpc=self.vpc
        )

        self.public_subnets = ec2.SubnetSelection(subnets=[
            ec2.Subnet.from_subnet_attributes(
                stack, 'staging-public-1d',
                subnet_id='subnet-0410d9b89444caacb'
            ),
            ec2.Subnet.from_subnet_attributes(
                stack, 'staging-public-1c',
                subnet_id='subnet-4cf42614'
            )
        ])

        self.private_subnets = ec2.SubnetSelection(subnets=[
            ec2.Subnet.from_subnet_attributes(
                stack, 'staging-nat-c',
                subnet_id='subnet-04bb071aa1282a42f'
            ),
            ec2.Subnet.from_subnet_attributes(
                stack, 'staging-nat-d',
                subnet_id='subnet-0b3081ee24472691d'
            )
        ])

        self.alb_certs = elb.ListenerCertificate.from_arn(
            'arn:aws:acm:ap-northeast-1:888777505088:certificate/4206b18e-4849-4ab0-b7ae-727bb5861c2d'
        )

        self.elb_log_bucket = s3.Bucket.from_bucket_name(
            stack, 'log',
            bucket_name='ietty-elb-logs'
        )

        self.cluster = ecs.Cluster.from_cluster_attributes(
            stack, 'staging-ecs',
            vpc=self.vpc,
            security_groups=[],
            cluster_name='staging-ecs'
        )

        self.execution_role = iam.Role.from_role_arn(
            stack, 'ecsTaskExecutionRole',
            role_arn='arn:aws:iam::888777505088:role/ecsTaskExecutionRole',
        )

        self.task_role_default = iam.Role.from_role_arn(
            stack, 'ecsTaskRole',
            role_arn='arn:aws:iam::888777505088:role/cdk-ecs-task-general',
        )

        self.efs_volume = {
            "name": "staging-efs02",
            "efs_volume_configuration": {
                "file_system_id": "fs-05372a0c16ac8afae"
            }
        }

        self.info_zone = route53.HostedZone.from_lookup(
            stack, 'ietty.info',
            domain_name='ietty.info',
            private_zone=False,
        )

        self.helth_ckeck_default = elb.HealthCheck(
            healthy_threshold_count=5,
            unhealthy_threshold_count=2,
            interval=Duration.seconds(30),
            timeout=Duration.seconds(5),
        )

        self.domain_ttl = Duration.minutes(1)
