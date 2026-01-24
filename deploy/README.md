# Infrastructure Deployment

## Structure

```
deploy/
├── main.yaml           # Main stack (orchestrates all nested stacks)
├── database.yaml       # DynamoDB table
├── messaging.yaml      # SNS + SQS resources
├── compute.yaml        # VPC + ALB + ECS Fargate
├── lambda.yaml         # Email processor Lambda (SAM)
├── local-test.yaml     # Minimal resources for local testing
└── README.md
```

## Prerequisites

1. AWS CLI configured with appropriate credentials
2. AWS SAM CLI installed (for Lambda deployment)
3. Docker running (for building Lambda)
4. S3 bucket for storing templates and Lambda code

## Deployment Steps

### 1. Create S3 bucket for templates

```bash
BUCKET_NAME=your-cfn-templates-bucket
aws s3 mb s3://${BUCKET_NAME}
```

### 2. Package SAM template (Lambda)

```bash
sam build --template-file deploy/lambda.yaml --build-dir .aws-sam/build

sam package \
  --template-file .aws-sam/build/template.yaml \
  --s3-bucket ${BUCKET_NAME} \
  --output-template-file deploy/packaged-lambda.yaml
```

### 3. Upload all templates to S3

```bash
STACK_NAME=order-processing-dev

aws s3 cp deploy/database.yaml s3://${BUCKET_NAME}/
aws s3 cp deploy/messaging.yaml s3://${BUCKET_NAME}/
aws s3 cp deploy/compute.yaml s3://${BUCKET_NAME}/
aws s3 cp deploy/packaged-lambda.yaml s3://${BUCKET_NAME}/lambda.yaml
```

### 4. Deploy main stack

```bash
aws cloudformation create-stack \
  --stack-name ${STACK_NAME} \
  --template-body file://deploy/main.yaml \
  --parameters \
    ParameterKey=Environment,ParameterValue=dev \
    ParameterKey=JWTSecretKey,ParameterValue=your-super-secret-jwt-key-min-32-chars \
  --capabilities CAPABILITY_IAM CAPABILITY_AUTO_EXPAND
```

**Note**: `CAPABILITY_AUTO_EXPAND` is required for SAM transforms in nested stacks.

### 5. Monitor deployment

```bash
aws cloudformation describe-stacks \
  --stack-name ${STACK_NAME} \
  --query 'Stacks[0].StackStatus'

aws cloudformation wait stack-create-complete --stack-name ${STACK_NAME}
```

### 6. Get stack outputs

```bash
aws cloudformation describe-stacks \
  --stack-name ${STACK_NAME} \
  --query 'Stacks[0].Outputs' --output table
```

## Environment Variables Flow

### ECS Fargate (Serverful)
Environment variables passed from CloudFormation → ECS Task:
- `DYNAMODB_TABLE_NAME`: From DatabaseStack output
- `SNS_TOPIC_ARN`: From MessagingStack output
- `JWT_SECRET_KEY`: From Secrets Manager (secure)
- `AWS_REGION`: Auto-populated
- `ENVIRONMENT`: From parameter

### Lambda (Serverless)
Environment variables passed from CloudFormation → Lambda:
- `DYNAMODB_TABLE_NAME`: From DatabaseStack output
- `FROM_EMAIL`: From parameter (SES verified email)

**IAM Permissions**:
- Lambda has DynamoDB read, SES send, SQS poll policies
- SQS queue policy allows SNS to send messages
- ECS task role has DynamoDB read/write, SNS publish

## Local Testing

Deploy minimal stack for local development:

```bash
aws cloudformation create-stack \
  --stack-name order-processing-local \
  --template-body file://deploy/local-test.yaml \
  --parameters ParameterKey=Environment,ParameterValue=local
```

Get resource names:
```bash
aws cloudformation describe-stacks \
  --stack-name order-processing-local \
  --query 'Stacks[0].Outputs' --output table
```

Set environment variables in `.env`:
```bash
DYNAMODB_TABLE_NAME=order-processing-local
SNS_TOPIC_ARN=arn:aws:sns:ap-south-1:123456789012:order-events-local
JWT_SECRET_KEY=your-local-jwt-secret-key
AWS_REGION=ap-south-1
```

## Update Stack

After code changes, rebuild and update:

```bash
# Package Lambda
sam build --template-file deploy/lambda.yaml --build-dir .aws-sam/build
sam package \
  --template-file .aws-sam/build/template.yaml \
  --s3-bucket ${BUCKET_NAME} \
  --output-template-file deploy/packaged-lambda.yaml

# Upload templates
aws s3 cp deploy/packaged-lambda.yaml s3://${BUCKET_NAME}/lambda.yaml

# Update stack
aws cloudformation update-stack \
  --stack-name ${STACK_NAME} \
  --template-body file://deploy/main.yaml \
  --parameters \
    ParameterKey=Environment,ParameterValue=dev \
    ParameterKey=JWTSecretKey,ParameterValue=your-super-secret-jwt-key-min-32-chars \
  --capabilities CAPABILITY_IAM CAPABILITY_AUTO_EXPAND
```

## Individual Stack Deployment

### Database only
```bash
aws cloudformation create-stack \
  --stack-name order-processing-db-dev \
  --template-body file://deploy/database.yaml \
  --parameters ParameterKey=Environment,ParameterValue=dev
```

### Messaging only
```bash
aws cloudformation create-stack \
  --stack-name order-processing-msg-dev \
  --template-body file://deploy/messaging.yaml \
  --parameters ParameterKey=Environment,ParameterValue=dev
```

### Lambda only (requires existing DynamoDB and SQS)
```bash
sam build --template-file deploy/lambda.yaml
sam deploy \
  --template-file .aws-sam/build/template.yaml \
  --stack-name order-processing-lambda-dev \
  --parameter-overrides \
    Environment=dev \
    DynamoDBTableName=order-processing-dev \
    SQSQueueArn=arn:aws:sqs:region:account:order-events-dev \
    FromEmail=noreply@example.com \
  --capabilities CAPABILITY_IAM
```

## Stack Deletion

```bash
# Delete main stack (deletes all nested stacks)
aws cloudformation delete-stack --stack-name ${STACK_NAME}

# Wait for deletion
aws cloudformation wait stack-delete-complete --stack-name ${STACK_NAME}

# Or delete individual stacks
aws cloudformation delete-stack --stack-name order-processing-local
```

## SES Email Setup

Before deploying, verify your email address in SES:

```bash
aws ses verify-email-identity --email-address noreply@example.com
```

Check verification status:
```bash
aws ses get-identity-verification-attributes \
  --identities noreply@example.com
```

For production, verify domain instead of individual emails.

## Troubleshooting

### Lambda not receiving messages
1. Check SQS queue policy allows SNS to send messages
2. Verify Lambda has SQS poller permissions
3. Check Lambda logs: `aws logs tail /aws/lambda/email-processor-dev --follow`

### ECS task not starting
1. Check CloudWatch logs: `/ecs/order-processing-dev`
2. Verify Secrets Manager has JWT secret
3. Ensure ECR image exists: `aws ecr describe-images --repository-name order-processing`

### Environment variables not set
1. Check stack outputs: `aws cloudformation describe-stacks --stack-name ${STACK_NAME}`
2. Verify nested stacks deployed successfully
3. Review ECS task definition environment section

## Cost Optimization

- **Local testing**: Only DynamoDB (on-demand), SNS, SQS - minimal cost
- **Dev**: Fargate Spot, 1 NAT Gateway, Lambda with low concurrency
- **Prod**: Fargate, multi-AZ NAT, Lambda reserved concurrency, CloudWatch detailed monitoring

## Security Notes

- JWT secret stored in Secrets Manager (encrypted)
- DynamoDB encrypted at rest with AWS managed keys
- SNS/SQS encrypted with AWS managed keys
- ECS tasks in private subnets
- ALB in public subnets only
- Security groups restrict traffic
- Lambda has least-privilege IAM policies
- SQS visibility timeout matches Lambda timeout
