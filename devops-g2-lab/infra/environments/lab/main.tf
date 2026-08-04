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
