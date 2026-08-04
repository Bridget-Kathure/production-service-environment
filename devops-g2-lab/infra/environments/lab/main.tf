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
  ingress_sg_id      = ""  # Will be set after B is created
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
  upstream_service   = "service-c"
  ingress_sg_id      = ""  # Will be set after A is created
  owner              = "service-b"
}

# ── Service A (behind ALB, calls B) ──────────────────────────
module "service_a" {
  source = "../../modules/ecs-service"

  service_name       = "a"
  group_number       = "g2"
  cluster_arn        = module.ecs_platform.cluster_arn
  vpc_id             = module.network.vpc_id
  private_subnet_ids = module.network.private_app_subnet_ids
  execution_role_arn = module.ecs_platform.execution_role_arn
  task_role_arn      = module.ecs_platform.task_role_arn
  image_tag          = "placeholder"
  app_port           = 3000
  desired_count      = 2
  namespace_id       = module.ecs_platform.namespace_id
  namespace_name     = module.ecs_platform.namespace_name
  upstream_service   = "service-b"
  alb_target_group_arn = module.alb.target_group_arn
  ingress_sg_id      = module.alb.alb_sg_id
  owner              = "service-a"
}
