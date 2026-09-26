# 🛒 MicroShop

**MicroShop** is a production-oriented e-commerce backend built with **Django, Django REST Framework, PostgreSQL, RabbitMQ, Redis, Celery, Nginx, Docker, and Kubernetes**.

The project is designed as a practical implementation of a **microservices architecture**, focusing not only on splitting an application into multiple services, but also on solving real distributed-system problems such as:

* Authentication and authorization
* Service-to-service communication
* Distributed transactions
* Saga Pattern
* Transactional Outbox Pattern
* Event-driven architecture
* Idempotent message processing
* Retry and Dead Letter Queue mechanisms
* Asynchronous background processing
* API Gateway
* Containerization
* Kubernetes orchestration
* Health checks and service discovery
* Independent databases per service

---

## 📐 Architecture

The current architecture consists of six Django microservices and several shared infrastructure components.

```text
                              ┌───────────────────┐
                              │      Client       │
                              └─────────┬─────────┘
                                        │
                                        ▼
                              ┌───────────────────┐
                              │   Nginx Gateway   │
                              │                   │
                              │ Authentication    │
                              │ Routing            │
                              │ Reverse Proxy      │
                              └─────────┬─────────┘
                                        │
              ┌─────────────────────────┼─────────────────────────┐
              │                         │                         │
              ▼                         ▼                         ▼
       ┌─────────────┐           ┌─────────────┐           ┌─────────────┐
       │    Auth     │           │   Catalog   │           │  Inventory  │
       │   Service   │           │   Service   │           │   Service   │
       └──────┬──────┘           └──────┬──────┘           └──────┬──────┘
              │                         │                         │
              ▼                         ▼                         ▼
        PostgreSQL                PostgreSQL                PostgreSQL


              ┌─────────────────────────┼─────────────────────────┐
              │                         │                         │
              ▼                         ▼                         ▼
       ┌─────────────┐           ┌─────────────┐           ┌─────────────┐
       │    Order    │           │   Payment   │           │Notification │
       │   Service   │           │   Service   │           │   Service   │
       └──────┬──────┘           └──────┬──────┘           └──────┬──────┘
              │                         │                         │
              ▼                         ▼                         ▼
        PostgreSQL                PostgreSQL                PostgreSQL


                         ┌─────────────────────┐
                         │      RabbitMQ        │
                         │                     │
                         │ Event Bus / Saga     │
                         └──────────┬──────────┘
                                    │
                         ┌──────────┴──────────┐
                         │                     │
                         ▼                     ▼
                    Event Consumers       Outbox Publishers


                         ┌─────────────────────┐
                         │       Redis         │
                         │                     │
                         │ Celery Broker       │
                         │ Result Backend      │
                         │ Cache               │
                         └─────────────────────┘
```

---

# 🧩 Microservices

## 1. Auth Service

Responsible for:

* User registration
* User authentication
* JWT token generation
* JWT refresh
* JWT verification
* User information
* Authentication-related authorization

Main technologies:

* Django
* Django REST Framework
* SimpleJWT
* PostgreSQL

Typical endpoints:

```text
POST /api/auth/register/
POST /api/auth/login/
POST /api/auth/refresh/
GET  /api/auth/me/
GET  /api/auth/verify/
GET  /health/
```

The Auth Service is also used by the Nginx Gateway to verify incoming JWT tokens.

---

## 2. Catalog Service

Responsible for product and category management.

Main entities:

```text
Category
Product
```

Responsibilities:

* Create categories
* Update categories
* Delete categories
* Create products
* Update products
* Delete products
* Retrieve products
* Retrieve categories

Authorization rules:

```text
GET       → Authenticated users
POST      → Admin
PUT/PATCH → Admin
DELETE    → Admin
```

The service uses PostgreSQL and Django ORM.

---

## 3. Inventory Service

Responsible for inventory management and product reservation.

Main entity:

```text
Inventory
```

The service tracks:

```text
quantity
reserved_quantity
available_quantity
```

Reservation operations use database transactions and row-level locking:

```python
transaction.atomic()
select_for_update()
```

This prevents race conditions when multiple orders try to reserve the same product simultaneously.

Inventory also participates in the Order Saga.

---

## 4. Order Service

The Order Service is the central coordinator of the order workflow.

Main entities:

```text
Order
OrderItem
OutboxEvent
ProcessedEvent
```

An order contains:

```text
user_id
status
total_price
created_at
updated_at
```

Order items store snapshots of:

```text
product_id
product_name
unit_price
quantity
total_price
```

This means historical orders do not depend on future changes to the Catalog Service.

---

## 5. Payment Service

Responsible for payment processing.

The current implementation simulates payment processing and participates in the distributed order workflow.

Main responsibilities:

* Receive payment requests
* Create payment records
* Process payment
* Publish payment success/failure events
* Participate in Saga compensation

---

## 6. Notification Service

Responsible for asynchronous notifications.

It uses:

* Django
* PostgreSQL
* RabbitMQ
* Celery
* Redis

Components:

```text
Notification API
RabbitMQ Consumer
Celery Worker
Celery Beat
```

Celery Beat is used for scheduled tasks such as cleanup of old notifications.

---

# 🔐 Authentication & Authorization

MicroShop uses **JWT-based authentication**.

The authentication flow is:

```text
Client
   │
   │ Authorization: Bearer <JWT>
   ▼
Nginx Gateway
   │
   │ auth_request
   ▼
Auth Service
   │
   │ JWT validation
   ▼
Nginx
   │
   │ Forward request
   ▼
Target Microservice
   │
   │ JWTAuthentication
   ▼
Django REST Framework
```

Authentication is intentionally validated at both gateway and application levels.

This provides defense in depth:

```text
Nginx
  ↓
Authentication check

Microservice
  ↓
Authentication check

Application
  ↓
Authorization
```

---

## JWT Secret Management

Each Django service has its own Django secret:

```text
AUTH_DJANGO_SECRET_KEY
CATALOG_DJANGO_SECRET_KEY
INVENTORY_DJANGO_SECRET_KEY
ORDER_DJANGO_SECRET_KEY
PAYMENT_DJANGO_SECRET_KEY
NOTIFICATION_DJANGO_SECRET_KEY
```

The JWT signing key is shared between services that need to validate JWTs:

```text
JWT_SIGNING_KEY
```

The distinction is:

```text
DJANGO_SECRET_KEY
    ↓
Specific Django application

JWT_SIGNING_KEY
    ↓
JWT authentication across services
```

---

# 🌐 API Gateway

Nginx is used as the central API Gateway.

The gateway provides:

* Reverse proxy
* Request routing
* JWT authentication integration
* Internal authentication endpoint
* Central entry point
* Service discovery through Docker/Kubernetes DNS

Example:

```text
/api/auth/*

        ↓

auth-service:8000


/api/catalog/*

        ↓

catalog-service:8000


/api/inventory/*

        ↓

inventory-service:8000


/api/orders/*

        ↓

order-service:8000


/api/payments/*

        ↓

payment-service:8000


/api/notifications/*

        ↓

notification-service:8000
```

Clients do not need to know the internal address of individual services.

---

# 📨 Event-Driven Architecture

MicroShop uses RabbitMQ as an event broker.

The main exchange is:

```text
microshop.events
```

The exchange uses the:

```text
topic
```

exchange type.

Main events include:

```text
order.created

inventory.reserved

inventory.reservation_failed

payment.requested

payment.succeeded

payment.failed

order.cancelled

inventory.release_requested
```

---

# 🔄 Order Saga

The order workflow is implemented using the **Saga Pattern**.

The complete workflow is:

```text
                    Order Created
                         │
                         ▼
                  order.created
                         │
                         ▼
                Inventory Service
                         │
                ┌────────┴────────┐
                │                 │
                ▼                 ▼
       inventory.reserved   reservation_failed
                │                 │
                ▼                 ▼
       payment.requested      Order Failed
                │
                ▼
         Payment Service
                │
          ┌─────┴─────┐
          │           │
          ▼           ▼
 payment.succeeded  payment.failed
          │           │
          ▼           ▼
       Order PAID   Order Failed
                      │
                      ▼
          inventory.release_requested
                      │
                      ▼
              Inventory Release
```

This avoids relying on a distributed database transaction across all microservices.

---

# 📦 Transactional Outbox

MicroShop implements the **Transactional Outbox Pattern** for reliable event publishing.

Without Outbox:

```text
Database Transaction
        │
        ├── Save Order
        │
        └── Publish RabbitMQ Event
```

If RabbitMQ fails after the database transaction succeeds, the event can be lost.

With Outbox:

```text
Database Transaction
        │
        ├── Save Order
        │
        └── Save OutboxEvent
                  │
                  ▼
            Outbox Publisher
                  │
                  ▼
               RabbitMQ
```

The database update and event creation happen inside the same transaction.

The publisher later sends unpublished events to RabbitMQ.

Services currently using Outbox include:

```text
Order
Inventory
Payment
```

---

# 🔁 Idempotent Event Processing

Distributed messaging can result in duplicate message delivery.

MicroShop therefore uses a `ProcessedEvent` model.

Conceptually:

```text
RabbitMQ Event
      │
      ▼
Check event_id
      │
 ┌────┴─────┐
 │          │
Exists     New
 │          │
 ▼          ▼
Ignore    Process
            │
            ▼
       Save event_id
```

This prevents the same business event from being processed multiple times.

---

# 💀 Retry & Dead Letter Queue

RabbitMQ consumers are designed to handle failures.

The general flow is:

```text
Main Queue
    │
    ▼
Consumer
    │
 ┌──┴───────────┐
 │              │
Success        Failure
 │              │
 ▼              ▼
 ACK        Retry Queue
                 │
                 ▼
              Retry
                 │
                 ▼
             Main Queue

After retry limit
        │
        ▼
       DLQ
```

This prevents temporary failures from immediately losing messages.

---

# ⚡ Redis & Celery

Redis is used as infrastructure for asynchronous tasks.

```text
Django
   │
   │ Celery Task
   ▼
 Redis
   │
   ▼
Celery Worker
   │
   ▼
Task Execution
```

Celery Beat is used for scheduled jobs.

For example:

```text
Celery Beat
     │
     │ 03:00
     ▼
cleanup_old_notifications
```

---

# 🗄️ Database Architecture

Each microservice owns its own PostgreSQL database.

```text
Auth         → auth_db
Catalog      → catalog_db
Inventory    → inventory_db
Order        → order_db
Payment      → payment_db
Notification → notification_db
```

The services do not directly access each other's databases.

```text
Auth Service       → Auth DB
Catalog Service    → Catalog DB
Inventory Service  → Inventory DB
Order Service      → Order DB
Payment Service    → Payment DB
Notification       → Notification DB
```

Cross-service communication happens through:

```text
HTTP
RabbitMQ Events
```

rather than direct database access.

---

# 🐳 Docker Compose

Docker Compose is used for local development and integration testing.

Infrastructure:

```text
Docker Compose
│
├── Auth Service
├── Catalog Service
├── Inventory Service
├── Order Service
├── Payment Service
├── Notification Service
│
├── PostgreSQL × 6
├── RabbitMQ
├── Redis
└── Nginx Gateway
```

The services communicate through the internal Docker network.

The microservices expose port `8000` internally, while Nginx acts as the public entry point.

---

# ☸️ Kubernetes

The project is also being deployed to Kubernetes.

The Kubernetes configuration is located in:

```text
k8s/
```

Current structure:

```text
k8s/
├── namespace.yaml
│
├── auth/
├── catalog/
├── inventory/
├── order/
├── payment/
├── notification/
│
├── gateway/
├── rabbitmq/
└── redis/
```

---

# 🧱 Kubernetes Resources

Each microservice generally contains:

```text
Deployment
Service
ConfigMap
Secret
PostgreSQL Deployment
PostgreSQL Service
PostgreSQL PVC
```

Services with asynchronous processing additionally contain:

```text
Consumer Deployment
Outbox Deployment
```

Notification also contains:

```text
Worker Deployment
Beat Deployment
Consumer Deployment
```

---

# 📁 Kubernetes Directory Structure

```text
k8s/
│
├── namespace.yaml
│
├── auth/
│   ├── app-secret.yaml
│   ├── configmap.yaml
│   ├── deployment.yaml
│   ├── postgres-deployment.yaml
│   ├── postgres-pvc.yaml
│   ├── postgres-service.yaml
│   ├── secret.yaml
│   └── service.yaml
│
├── catalog/
│   ├── app-secret.yaml
│   ├── configmap.yaml
│   ├── deployment.yaml
│   ├── postgres-deployment.yaml
│   ├── postgres-pvc.yaml
│   ├── postgres-service.yaml
│   ├── secret.yaml
│   └── service.yaml
│
├── inventory/
│   ├── app-secret.yaml
│   ├── configmap.yaml
│   ├── consumer-deployment.yaml
│   ├── deployment.yaml
│   ├── outbox-deployment.yaml
│   ├── postgres-deployment.yaml
│   ├── postgres-pvc.yaml
│   ├── postgres-service.yaml
│   ├── secret.yaml
│   └── service.yaml
│
├── order/
│   ├── app-secret.yaml
│   ├── configmap.yaml
│   ├── consumer-deployment.yaml
│   ├── deployment.yaml
│   ├── outbox-deployment.yaml
│   ├── postgres-deployment.yaml
│   ├── postgres-pvc.yaml
│   ├── postgres-service.yaml
│   ├── secret.yaml
│   └── service.yaml
│
├── payment/
│   ├── app-secret.yaml
│   ├── configmap.yaml
│   ├── consumer-deployment.yaml
│   ├── deployment.yaml
│   ├── outbox-deployment.yaml
│   ├── postgres-deployment.yaml
│   ├── postgres-pvc.yaml
│   ├── postgres-service.yaml
│   ├── secret.yaml
│   └── service.yaml
│
├── notification/
│   ├── app-secret.yaml
│   ├── beat-deployment.yaml
│   ├── configmap.yaml
│   ├── consumer-deployment.yaml
│   ├── deployment.yaml
│   ├── postgres-deployment.yaml
│   ├── postgres-pvc.yaml
│   ├── postgres-service.yaml
│   ├── secret.yaml
│   ├── service.yaml
│   └── worker-deployment.yaml
│
├── gateway/
│   ├── configmap.yaml
│   ├── deployment.yaml
│   └── service.yaml
│
├── rabbitmq/
│   ├── deployment.yaml
│   ├── pvc.yaml
│   ├── secret.yaml
│   └── service.yaml
│
└── redis/
    ├── deployment.yaml
    ├── pvc.yaml
    └── service.yaml
```

---

# 🔑 Kubernetes Secrets

Secrets are separated according to their responsibility.

Application secrets include:

```text
DJANGO_SECRET_KEY
JWT_SIGNING_KEY
```

Database secrets include:

```text
POSTGRES_PASSWORD
```

RabbitMQ secrets include:

```text
RABBITMQ_USERNAME
RABBITMQ_PASSWORD
```

For local development, Kubernetes `Secret` resources are used.

For production environments, a dedicated secret-management solution should be considered instead of committing real credentials to Git.

---

# 🌐 Kubernetes Service Discovery

Kubernetes Services provide internal DNS-based service discovery.

For example:

```text
auth-service:8000
catalog-service:8000
inventory-service:8000
order-service:8000
payment-service:8000
notification-service:8000
```

PostgreSQL services:

```text
auth-db:5432
catalog-db:5432
inventory-db:5432
order-db:5432
payment-db:5432
notification-db:5432
```

Infrastructure:

```text
rabbitmq:5672
redis:6379
```

This means applications do not need hardcoded Pod IP addresses.

---

# 🚀 Running with Docker Compose

Clone the project:

```bash
git clone git@github.com:SoheilHooshmand/MicroShop.git
cd MicroShop
```

Create the required `.env` files for the services.

Build the services:

```bash
docker compose build
```

Start the complete stack:

```bash
docker compose up -d
```

Check containers:

```bash
docker compose ps
```

Check logs:

```bash
docker compose logs -f
```

Check a specific service:

```bash
docker compose logs -f auth-service
```

Stop the stack:

```bash
docker compose down
```

---

# 🧪 Testing the Services

Check service health through the gateway:

```bash
curl http://localhost/health/
```

For authenticated endpoints:

```bash
curl \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  http://localhost/api/auth/me/
```

---

# ☸️ Running with Minikube

The Kubernetes configuration is designed to be usable with Minikube for local development.

Start Minikube:

```bash
minikube start --driver=docker
```

Check the cluster:

```bash
kubectl get nodes
```

Create the namespace:

```bash
kubectl apply -f k8s/namespace.yaml
```

Check:

```bash
kubectl get namespaces
```

---

# 🐳 Loading Images into Minikube

Build an image:

```bash
docker compose build auth-service
```

Load it into Minikube:

```bash
minikube image load microshop-auth-service:latest
```

Repeat for the other services:

```bash
docker compose build catalog-service
docker compose build inventory-service
docker compose build order-service
docker compose build payment-service
docker compose build notification-service
```

Then:

```bash
minikube image load microshop-catalog-service:latest
minikube image load microshop-inventory-service:latest
minikube image load microshop-order-service:latest
minikube image load microshop-payment-service:latest
minikube image load microshop-notification-service:latest
```

---

# 📦 Deploying Kubernetes Resources

Apply the namespace:

```bash
kubectl apply -f k8s/namespace.yaml
```

Deploy infrastructure first:

```bash
kubectl apply -f k8s/rabbitmq/
kubectl apply -f k8s/redis/
```

Then deploy databases:

```bash
kubectl apply -f k8s/auth/postgres-pvc.yaml
kubectl apply -f k8s/auth/postgres-deployment.yaml
kubectl apply -f k8s/auth/postgres-service.yaml
```

The same process can be applied to the other services.

Then deploy application services:

```bash
kubectl apply -f k8s/auth/
kubectl apply -f k8s/catalog/
kubectl apply -f k8s/inventory/
kubectl apply -f k8s/order/
kubectl apply -f k8s/payment/
kubectl apply -f k8s/notification/
```

Finally deploy the gateway:

```bash
kubectl apply -f k8s/gateway/
```

---

# 🔍 Kubernetes Debugging

List all Pods:

```bash
kubectl get pods -n microshop
```

List Deployments:

```bash
kubectl get deployments -n microshop
```

List Services:

```bash
kubectl get services -n microshop
```

List PVCs:

```bash
kubectl get pvc -n microshop
```

Check Pod details:

```bash
kubectl describe pod <POD_NAME> -n microshop
```

Check logs:

```bash
kubectl logs <POD_NAME> -n microshop
```

Follow logs:

```bash
kubectl logs -f <POD_NAME> -n microshop
```

Check recent cluster events:

```bash
kubectl get events -n microshop --sort-by=.lastTimestamp
```

---

# 🩺 Health Checks

Django services expose:

```text
/health/
```

Kubernetes uses health probes such as:

```yaml
readinessProbe:
  httpGet:
    path: /health/
    port: 8000
```

and:

```yaml
livenessProbe:
  httpGet:
    path: /health/
    port: 8000
```

The distinction is:

```text
Liveness
    ↓
Is the application alive?

Readiness
    ↓
Is the application ready to receive traffic?
```

---

# 🔒 Authorization Model

MicroShop distinguishes authentication from authorization.

### Authentication

Answers:

> Who is this user?

Handled using JWT.

### Authorization

Answers:

> Is this user allowed to perform this operation?

Examples:

```text
Authenticated User
        │
        ├── GET products
        │
        └── GET orders


Admin
        │
        ├── Create product
        ├── Update product
        ├── Delete product
        └── Manage catalog
```

Order ownership is also enforced:

```text
User A
   │
   ├── Order 1 → allowed
   └── Order 2 → forbidden
```

unless the user has the appropriate administrative privileges.

---

# 🛡️ Concurrency Control

Inventory operations are sensitive to race conditions.

For example:

```text
Inventory = 10

Request A → reserve 7
Request B → reserve 5
```

Without row locking, both requests may read:

```text
available = 10
```

and incorrectly succeed.

The Inventory Service therefore uses:

```python
transaction.atomic()
select_for_update()
```

Conceptually:

```text
Request A
   │
   ▼
Lock Inventory Row
   │
   ▼
Check Available Quantity
   │
   ▼
Update Reservation
   │
   ▼
Commit
   │
   ▼
Release Lock

Request B
   │
   ▼
Wait for Lock
```

---

# 🧠 Design Principles

The project follows several important distributed-system principles.

### Database per Service

Each service owns its data.

### Eventual Consistency

Cross-service state is synchronized through events rather than distributed database transactions.

### Idempotency

Consumers can safely handle duplicate events.

### Fault Tolerance

RabbitMQ retry queues and DLQs handle temporary failures.

### Transactional Consistency

Outbox events are created in the same transaction as business changes.

### Defense in Depth

JWT authentication is checked at both gateway and service level.

### Service Isolation

A service does not directly access another service's database.

---

# 📊 Technology Stack

| Component               | Technology            |
| ----------------------- | --------------------- |
| Backend                 | Django                |
| API                     | Django REST Framework |
| Authentication          | JWT / SimpleJWT       |
| Database                | PostgreSQL            |
| Message Broker          | RabbitMQ              |
| Async Tasks             | Celery                |
| Cache / Celery Backend  | Redis                 |
| API Gateway             | Nginx                 |
| Containerization        | Docker                |
| Local Orchestration     | Docker Compose        |
| Container Orchestration | Kubernetes            |
| Local Kubernetes        | Minikube              |
| Programming Language    | Python                |
| Database Access         | Django ORM            |
| Distributed Workflow    | Saga Pattern          |
| Reliable Messaging      | Transactional Outbox  |
| Message Idempotency     | ProcessedEvent        |

---

# 📈 Project Roadmap

The project is being developed incrementally.

```text
[x] Django Microservices
[x] PostgreSQL per Service
[x] Docker Compose
[x] RabbitMQ
[x] Event-Driven Architecture
[x] Saga Pattern
[x] Transactional Outbox
[x] Idempotent Consumers
[x] Retry / DLQ
[x] Redis
[x] Celery
[x] Nginx API Gateway
[x] JWT Authentication
[x] Authorization
[x] Kubernetes Base Configuration
[ ] Complete Kubernetes Deployment
[ ] Kubernetes Migration Jobs
[ ] Kubernetes Health Checks
[ ] Horizontal Pod Autoscaling
[ ] Network Policies
[ ] Monitoring
[ ] Centralized Logging
[ ] Helm Charts
[ ] CI/CD
```

---

# 🏗️ Future Kubernetes Architecture

The planned Kubernetes architecture is:

```text
                         Internet / Client
                                │
                                ▼
                       ┌─────────────────┐
                       │  Nginx Gateway  │
                       └────────┬────────┘
                                │
        ┌───────────────────────┼────────────────────────┐
        │                       │                        │
        ▼                       ▼                        ▼
      Auth                   Catalog                  Inventory
        │                       │                        │
        ▼                       ▼                        ▼
      Auth DB               Catalog DB              Inventory DB


        ┌───────────────────────┼────────────────────────┐
        │                       │                        │
        ▼                       ▼                        ▼
      Order                  Payment               Notification
        │                       │                        │
        ▼                       ▼                        ▼
    Order DB                Payment DB             Notification DB


                     ┌────────────────────┐
                     │      RabbitMQ      │
                     └────────────────────┘

                     ┌────────────────────┐
                     │       Redis        │
                     └────────────────────┘
```

Future infrastructure can additionally include:

```text
Ingress
Horizontal Pod Autoscaler
NetworkPolicy
Prometheus
Grafana
Centralized Logging
Helm
CI/CD
```

---

# 🎯 Project Goals

MicroShop is intended to demonstrate practical knowledge of:

* Microservices Architecture
* Django REST Framework
* Distributed Systems
* Event-Driven Architecture
* RabbitMQ
* Saga Pattern
* Transactional Outbox
* Idempotent Message Processing
* PostgreSQL
* Redis
* Celery
* JWT Authentication
* API Gateway
* Docker
* Kubernetes
* Service Discovery
* Container Orchestration
* Distributed Transaction Management
* Concurrency Control
* Fault Tolerance

The project is designed as a portfolio and learning project with an emphasis on understanding **why** each architectural component exists rather than simply assembling technologies together.

---

# 👨‍💻 Author

**Soheil Hooshmand**

Computer Engineering — Amirkabir University of Technology

Backend Developer | Django | Distributed Systems | AI/ML

GitHub:

`https://github.com/SoheilHooshmand`

LinkedIn:

`https://www.linkedin.com/in/soheil-hooshmand/`

---

# 📄 License

This project is intended for educational and portfolio purposes.
