locals {
  name_prefix = "devops-${var.group_number}"
}

resource "aws_security_group" "alb" {
  name        = "${local.name_prefix}-alb-sg-iac"
  description = "ALB - public HTTP only"
  vpc_id      = var.vpc_id

  ingress {
    description = "HTTP from internet"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # No inline egress - proper SG-referenced egress added in main.tf

  tags = {
    Name  = "${local.name_prefix}-alb-sg-iac"
    Owner = var.owner
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_lb" "main" {
  name               = "${local.name_prefix}-alb-iac"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = var.public_subnet_ids

  enable_deletion_protection = false

  tags = {
    Name  = "${local.name_prefix}-alb-iac"
    Owner = var.owner
  }
}

resource "aws_lb_target_group" "service_a" {
  name        = "${local.name_prefix}-service-a-tg-iac"
  port        = var.app_port
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"

  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    matcher             = "200"
    path                = "/"
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = 5
    unhealthy_threshold = 2
  }

  tags = {
    Name  = "${local.name_prefix}-service-a-tg-iac"
    Owner = "service-a"
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.service_a.arn
  }
}
