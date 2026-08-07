locals {
  name_prefix = "devops-${var.group_number}"
  full_name   = "${local.name_prefix}-service-${var.service_name}"
  ecr_repo    = "${local.name_prefix}-service-${var.service_name}-iac"
  port_name   = "${local.full_name}-port"
}

data "aws_caller_identity" "current" {}

resource "aws_ecr_repository" "main" {
  name                 = local.ecr_repo
  image_tag_mutability = "IMMUTABLE"
  image_scanning_configuration {
    scan_on_push = true
  }
  tags = {
    Name  = local.ecr_repo
    Owner = "service-${var.service_name}"
  }
}

resource "aws_cloudwatch_log_group" "main" {
  name              = "/ecs/${local.full_name}"
  retention_in_days = 7
  tags = {
    Name  = "/ecs/${local.full_name}"
    Owner = "service-${var.service_name}"
  }
}

resource "aws_security_group" "main" {
  name        = "${local.full_name}-sg"
  description = "Service ${upper(var.service_name)} security group"
  vpc_id      = var.vpc_id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name  = "${local.full_name}-sg"
    Owner = "service-${var.service_name}"
  }
}


resource "aws_ecs_task_definition" "main" {
  family                   = local.full_name
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.cpu
  memory                   = var.memory
  execution_role_arn       = var.execution_role_arn
  task_role_arn            = var.task_role_arn

  container_definitions = jsonencode([
    {
      name      = local.full_name
      image     = "${data.aws_caller_identity.current.account_id}.dkr.ecr.us-east-2.amazonaws.com/${local.ecr_repo}:${var.image_tag}"
      essential = true
      portMappings = [
        {
          name          = local.port_name
          containerPort = var.app_port
          protocol      = "tcp"
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.main.name
          "awslogs-region"        = "us-east-2"
          "awslogs-stream-prefix" = "ecs"
        }
      }
      environment = [
        { name = "SERVICE_NAME", value = var.service_name },
        { name = "UPSTREAM_SERVICE", value = var.upstream_service },
        { name = "APP_PORT", value = tostring(var.app_port) }
      ]
    }
  ])

  tags = {
    Name  = local.full_name
    Owner = "service-${var.service_name}"
  }
}

resource "aws_ecs_service" "main" {
  name            = local.full_name
  cluster         = var.cluster_arn
  task_definition = aws_ecs_task_definition.main.arn
  desired_count   = var.desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [aws_security_group.main.id]
    assign_public_ip = false
  }

  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }

  dynamic "load_balancer" {
    for_each = var.alb_target_group_arn != "" ? [1] : []
    content {
      target_group_arn = var.alb_target_group_arn
      container_name   = local.full_name
      container_port   = var.app_port
    }
  }

  dynamic "service_connect_configuration" {
    for_each = var.namespace_id != "" ? [1] : []
    content {
      enabled   = true
      namespace = var.namespace_name
      service {
        port_name      = local.port_name
        discovery_name = "service-${var.service_name}-iac"
        client_alias {
          port     = var.app_port
          dns_name = "service-${var.service_name}-iac"
        }
      }
    }
  }

  tags = {
    Name  = local.full_name
    Owner = "service-${var.service_name}"
  }

  lifecycle {
    postcondition {
      condition     = self.network_configuration[0].assign_public_ip == false
      error_message = "Architecture rule violated: ECS service must not receive a public IP (assign_public_ip must be false)."
    }
  }
}
