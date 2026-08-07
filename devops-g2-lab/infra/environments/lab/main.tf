module "network" {
  source = "../../modules/network"

  group_number = "g2"
  owner        = "platform"
}

module "alb" {
  source = "../../modules/alb"

  group_number      = "g2"
  vpc_id            = module.network.vpc_id
  public_subnet_ids = module.network.public_subnet_ids
  app_port          = 3000
  owner             = "platform"
}

module "ecs_platform" {
  source = "../../modules/ecs-platform"

  group_number = "g2"
  vpc_id       = module.network.vpc_id
  owner        = "platform"
}

# ── Service C (leaf - no upstream) ───────────────────────────
module "service_c" {
  source = "../../modules/ecs-service"

  service_name       = "c"
  group_number       = "g2"
  cluster_arn        = module.ecs_platform.cluster_arn
  vpc_id             = module.network.vpc_id
  private_subnet_ids = module.network.private_app_subnet_ids
  execution_role_arn = module.ecs_platform.execution_role_arn
  task_role_arn      = module.ecs_platform.task_role_arn
  image_tag          = "placeholder"
  app_port           = 3003
  desired_count      = 1
  namespace_id       = module.ecs_platform.namespace_id
  namespace_name     = module.ecs_platform.namespace_name
  upstream_service   = ""
  owner              = "service-c"
}

# ── Service B (calls C) ──────────────────────────────────────
module "service_b" {
  source = "../../modules/ecs-service"

  service_name       = "b"
  group_number       = "g2"
  cluster_arn        = module.ecs_platform.cluster_arn
  vpc_id             = module.network.vpc_id
  private_subnet_ids = module.network.private_app_subnet_ids
  execution_role_arn = module.ecs_platform.execution_role_arn
  task_role_arn      = module.ecs_platform.task_role_arn
  image_tag          = "placeholder"
  app_port           = 3002
  desired_count      = 1
  namespace_id       = module.ecs_platform.namespace_id
  namespace_name     = module.ecs_platform.namespace_name
  upstream_service   = "service-c-iac"
  owner              = "service-b"
}

# ── Service A (behind ALB, calls B) ──────────────────────────
module "service_a" {
  source = "../../modules/ecs-service"

  service_name         = "a"
  group_number         = "g2"
  cluster_arn          = module.ecs_platform.cluster_arn
  vpc_id               = module.network.vpc_id
  private_subnet_ids   = module.network.private_app_subnet_ids
  execution_role_arn   = module.ecs_platform.execution_role_arn
  task_role_arn        = module.ecs_platform.task_role_arn
  image_tag            = "placeholder"
  app_port             = 3000
  desired_count        = 2
  namespace_id         = module.ecs_platform.namespace_id
  namespace_name       = module.ecs_platform.namespace_name
  upstream_service     = "service-b-iac"
  alb_target_group_arn = module.alb.target_group_arn
  owner                = "service-a"
}

# ── Security Group Rules (proper SG references) ──────────────

# ALB -> Service A
resource "aws_security_group_rule" "alb_to_a" {
  type                     = "egress"
  from_port                = 3000
  to_port                  = 3000
  protocol                 = "tcp"
  source_security_group_id = module.service_a.security_group_id
  security_group_id        = module.alb.alb_sg_id
  description              = "ALB to Service A"
}

# Service A <- ALB
resource "aws_security_group_rule" "a_from_alb" {
  type                     = "ingress"
  from_port                = 3000
  to_port                  = 3000
  protocol                 = "tcp"
  source_security_group_id = module.alb.alb_sg_id
  security_group_id        = module.service_a.security_group_id
  description              = "Service A from ALB"
}

# Service A -> Service B

# Service B <- Service A
resource "aws_security_group_rule" "b_from_a" {
  type                     = "ingress"
  from_port                = 3002
  to_port                  = 3002
  protocol                 = "tcp"
  source_security_group_id = module.service_a.security_group_id
  security_group_id        = module.service_b.security_group_id
  description              = "Service B from Service A"
}

# Service B -> Service C

# Service C <- Service B
resource "aws_security_group_rule" "c_from_b" {
  type                     = "ingress"
  from_port                = 3003
  to_port                  = 3003
  protocol                 = "tcp"
  source_security_group_id = module.service_b.security_group_id
  security_group_id        = module.service_c.security_group_id
  description              = "Service C from Service B"
}
