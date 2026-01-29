# Order Processing System

A production-ready serverless order processing system built on AWS that handles order placement, payment processing, and asynchronous fulfillment with automated email notifications.

## Statement

1. Design a backend order processing system that handles order placement, payment confirmation, and fulfilment.
2. Track order status throughout its lifecycle and process fulfilment asynchronously.
3. Notify Users as the order progresses or when failure occurs.

## Assumptions

This service is designed as a core component of an e-commerce platform that expects consistent 24x7 traffic load. The architecture choice of ECS Fargate over Lambda for the REST API is driven by:

- **Consistent Load**: E-commerce platforms experience continuous traffic rather than sporadic bursts, making containerized workloads more cost-effective than Lambda's per-invocation pricing model
- **Low Latency Requirements**: Order placement and payment processing require sub-100ms response times; ECS eliminates Lambda cold starts and provides predictable performance
- **Stateful Connections**: Long-running container instances maintain warm database connections and JWT validation caches, reducing per-request overhead

Lambda is still used for asynchronous email notifications where sporadic execution and cold start latency are acceptable trade-offs for cost efficiency.

## Overview

This system implements an event-driven architecture that tracks order status throughout its lifecycle and notifies users as orders progress through various stages (created, payment confirmed, fulfillment started, completed, or cancelled).

## Architecture

### Serverful Component (ECS Fargate)
- **FastAPI REST API** running on AWS ECS Fargate with Application Load Balancer
- Handles synchronous operations: order creation, payment processing, order management
- JWT-based authentication with role-based access control (Customer, Staff, Admin)
- Auto-scaling based on ALB request count per target (1-3 tasks)

### Serverless Component (Lambda)
- **Email Processor Lambda** triggered by SQS messages
- Processes order events asynchronously and sends email notifications via SES
- Batch failure handling with dead letter queue for failed messages

### Data Flow
1. Client submits order via REST API (ECS)
2. Order stored in DynamoDB with status tracking
3. Event published to SNS topic
4. SNS delivers message to SQS queue
5. Lambda processes queue messages and sends email notifications
6. Failed messages moved to DLQ after 3 retry attempts

## AWS Infrastructure

### Compute
- **ECS Fargate**: Containerized REST API with FARGATE and FARGATE_SPOT capacity providers
- **Lambda**: Python 3.12 runtime for asynchronous email processing
- **Application Load Balancer**: Internet-facing load balancer in public subnets

### Storage
- **DynamoDB**: Single-table design with PAY_PER_REQUEST billing, streams enabled
- **ECR**: Container image registry

### Messaging
- **SNS**: Order events topic for pub/sub messaging
- **SQS**: Order events queue with 5-minute visibility timeout
- **SQS DLQ**: Dead letter queue with 3 max receive count

### Security
- **ACM Certificate**: HTTPS enabled with TLS 1.2+ on ALB (HTTP auto-redirects to HTTPS)
- **AWS WAF**: Rate limiting (500 requests per 5 minutes per IP) with DDoS protection
- **Secrets Manager**: JWT secret key storage
- **IAM Roles**: Task execution role (ECR, Secrets Manager) and task role (DynamoDB, SNS)
- **Security Groups**: ALB accepts port 80/443 from internet, ECS tasks only accept from ALB
- **Network Isolation**: ECS tasks in private subnets, ALB in public subnets

### Monitoring
- **CloudWatch Logs**: 7-day retention for ECS task logs
- **Health Checks**: ALB target group health checks on /health endpoint (30s interval, 3 retries)
- **WAF Metrics**: Rate limit violations and blocked requests tracked in CloudWatch

## Key Features

### Order Lifecycle Management
- **Order States**: PENDING, PAYMENT_CONFIRMED, FULFILLMENT_STARTED, COMPLETED, CANCELLED
- **Status Transitions**: Validated state machine prevents invalid transitions
- **Audit Trail**: All state changes tracked with timestamps

### Authentication & Authorization
- **JWT Tokens**: HS256 algorithm with 24-hour expiration
- **Role-Based Access**:
  - Customer: Create orders, view own orders, process payments
  - Staff: View all orders, update fulfillment status
  - Admin: User management, create staff accounts

### Auto-Scaling
- **Target Metric**: 100 requests per second per task
- **Scaling Behavior**: 
  - Scale out cooldown: 300 seconds
  - Scale in cooldown: 300 seconds
  - Min tasks: 1, Max tasks: 3

### Email Notifications
Email sent for these events:
- ORDER_CREATED
- PAYMENT_CONFIRMED
- PAYMENT_FAILED
- FULFILLMENT_STARTED
- FULFILLMENT_COMPLETED
- ORDER_CANCELLED

## Screenshots
1. Order Confirmation  
<img width="576" height="683" alt="order_placed_confirmation" src="https://github.com/user-attachments/assets/4d5d5c42-420b-4afe-8c77-3081143a3c86" />

2. Order Cancelled
<img width="578" height="688" alt="order_cancelled" src="https://github.com/user-attachments/assets/df997a0c-fb7b-4830-99b3-eda1222eff98" />

3. Order Payment Success
<img width="579" height="682" alt="order_payment_success" src="https://github.com/user-attachments/assets/f4257ab1-84cb-4481-97e2-8f162bcc1989" />

4. Order Payment Failed
<img width="590" height="673" alt="order_payment_fail" src="https://github.com/user-attachments/assets/66af093a-e26f-4152-9066-1591e812d59e" />

5. Order Fulfillment Started
<img width="580" height="691" alt="order_fulfillment_start" src="https://github.com/user-attachments/assets/f59af8b5-d587-48a3-8450-e108390ca2fe" />

6. Order Fulfillment Cancelled
<img width="587" height="691" alt="order_fulfilment_cancelled" src="https://github.com/user-attachments/assets/0d2c57fd-5777-47b4-870d-69a8698dcc32" />

7. Order Fulfilment Completed
<img width="587" height="684" alt="order_fulfilled" src="https://github.com/user-attachments/assets/d57b9f0d-87c4-4e18-8942-1c583da8288e" />


### Error Handling
- **Deployment Circuit Breaker**: Automatic rollback on failed deployments
- **SQS Retry Logic**: 3 attempts before moving to DLQ
- **Lambda Batch Failures**: Partial batch failure reporting to prevent entire batch reprocessing

## API Endpoints

### Public
- `GET /health` - Health check endpoint
- `POST /auth/register` - User registration
- `POST /auth/login` - User authentication

### Customer (Authenticated)
- `POST /orders` - Create new order
- `GET /orders` - List user's orders
- `GET /orders/{order_id}` - Get order details
- `POST /orders/{order_id}/payment` - Process payment
- `DELETE /orders/{order_id}` - Cancel order
- `GET /orders/track/{order_id}` - Track order status

### Staff (Authenticated)
- `PATCH /orders/{order_id}/fulfilment` - Update fulfillment status (start/complete/cancel)
- `GET /orders/all` - List all orders
- `GET /orders/order/{order_id}` - Get any order by ID
- `GET /orders/{order_status}` - Filter orders by status

### Admin (Authenticated)
- `GET /admin/users` - List all users
- `POST /admin/users/staff` - Create staff or admin user
- `DELETE /admin/users/{user_id}` - Delete user account

## Project Structure

```
order-processing-system/
├── app/
│   ├── serverful/              # ECS FastAPI application
│   │   ├── controllers/        # API route handlers
│   │   ├── services/           # Business logic layer
│   │   ├── repositories/       # Data access layer
│   │   ├── models/             # Pydantic models and DTOs
│   │   ├── utils/              # JWT, password hashing, error handlers
│   │   ├── dependencies/       # Dependency injection
│   │   ├── config/             # Application configuration
│   │   ├── lifespan.py         # Startup/shutdown lifecycle
│   │   └── main.py             # FastAPI application entry point
│   └── serverless/
│       └── email-processor/    # Lambda function
│           ├── handler.py      # Lambda entry point
│           ├── service.py      # Email template and SES logic
│           └── models.py       # Event models
├── deploy/
│   └── complete-stack.yaml     # CloudFormation template (ECS + infrastructure)
├── tests/                      # Unit tests (98% coverage, 189 tests)
├── Dockerfile                  # Container image definition
├── requirements.txt            # Python dependencies
└── pytest.ini                  # Test configuration
```

## Deployment

### Prerequisites
- AWS CLI configured with appropriate credentials
- ECR repository created
- VPC with public and private subnets
- SES email address verified
- JWT secret stored in Secrets Manager

### Deploy Infrastructure

```bash
# Build and push Docker image
docker build -t order-processing-system .
aws ecr get-login-password --region ap-south-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.ap-south-1.amazonaws.com
docker tag order-processing-system:latest <account-id>.dkr.ecr.ap-south-1.amazonaws.com/order-processing-system:latest
docker push <account-id>.dkr.ecr.ap-south-1.amazonaws.com/order-processing-system:latest

# Deploy CloudFormation stack
aws cloudformation create-stack \
  --stack-name order-processing-system \
  --template-body file://deploy/complete-stack.yaml \
  --parameters \
    ParameterKey=VpcId,ParameterValue=<vpc-id> \
    ParameterKey=SubnetIds,ParameterValue=<private-subnet-1>,<private-subnet-2> \
    ParameterKey=PublicSubnetIds,ParameterValue=<public-subnet-1>,<public-subnet-2> \
    ParameterKey=ECRImageUri,ParameterValue=<ecr-image-uri> \
    ParameterKey=JWTSecretArn,ParameterValue=<secrets-manager-arn> \
  --capabilities CAPABILITY_NAMED_IAM \
  --region ap-south-1
```

## Configuration Parameters

- `CertificateArn`: ACM certificate ARN for HTTPS (leave empty for HTTP only)
- `EnableWAF`: Enable AWS WAF with rate limiting (default: true)
- `DesiredCount`: Initial number of ECS tasks (default: 1)
- `MinTaskCount`: Minimum tasks for auto-scaling (default: 1)
- `MaxTaskCount`: Maximum tasks for auto-scaling (default: 3)
- `TargetRequestsPerSecond`: Target requests per task for scaling (default: 100)
- `ContainerPort`: Application port (default: 8000)
- `SESFromEmail`: Verified SES email address for notifications

## Testing

### POSTMAN TRACK ORDER PERFORMANCE TESTING REPORT 
<img width="1028" height="879" alt="track-order-endpoint-performance" src="https://github.com/user-attachments/assets/3e1ae232-7e6e-4dc6-b35d-7e3b51a1c074" />
1. Avg response time of 49 ms 
2. Load tested for approx 261 req per sec 
3. Total req served 25,560
4. Strongly optimized read requests (access patterns)


```bash
# Run all tests with coverage
pytest --cov=app --cov-report=term-missing

# Run specific test module
pytest tests/test_services/test_order_service.py -v
```

Test coverage: 98% across 189 tests

## Security Considerations

### Current Implementation
- **HTTPS with TLS**: ACM certificate configured on ALB with HTTP to HTTPS redirect
- **AWS WAF**: Rate-based rule limiting 500 requests per 5 minutes per IP
- **Secrets Management**: JWT tokens stored in AWS Secrets Manager
- **IAM Least Privilege**: Separate task execution and task roles with minimal permissions
- **Network Isolation**: ECS tasks in private subnets, only accessible via ALB
- **Security Groups**: Restrictive ingress rules (ECS only accepts from ALB security group)
- **No Hardcoded Secrets**: All credentials injected via environment variables from Secrets Manager




