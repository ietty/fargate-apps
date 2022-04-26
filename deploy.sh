docker rm -vf cdk 
docker run -d --name cdk \
  -v ~/.aws:/home/docker/.aws \
  -v ~/.git-credentials:/home/docker/.git-credentials \
  -v ~/.gitconfig:/home/docker/.gitconfig \
  -v ~/devbase/opt/fargate-apps:/home/docker/app \
  -e CDK_DEFAULT_ACCOUNT=888777505088 \
  -e CDK_DEFAULT_REGION=ap-northeast-1 \
  ietty/awscdkv2:2022041701 tail -f /dev/null

