# Native Terraform tests for modules/ecs-service.
# Runs entirely against a mocked AWS provider (Terraform >= 1.7), so
# `terraform test` works with no AWS credentials and no real account -
# useful while credentials are unavailable, and cheap enough to run in CI.
#
# Run with:  terraform test tests/ecs_service.tftest.hcl
# (from infra/, or `terraform -chdir=infra test tests/...`)

mock_provider "aws" {}

variables {
  service_name       = "a"
  cluster_arn        = "arn:aws:ecs:us-east-2:827478161993:cluster/mock-cluster"
  vpc_id             = "vpc-mock00000000"
  private_subnet_ids = ["subnet-mockaz1", "subnet-mockaz2"]
  execution_role_arn = "arn:aws:iam::827478161993:role/mock-exec-role"
  task_role_arn      = "arn:aws:iam::827478161993:role/mock-task-role"
  namespace_id       = "ns-mock0000000000"
  namespace_name     = "group2.internal"
  owner              = "service-a"
  image_tag          = "abc1234"
}

run "rejects_latest_image_tag" {
  command = plan

  module {
    source = "./modules/ecs-service"
  }

  variables {
    image_tag = "latest"
  }

  expect_failures = [
    var.image_tag,
  ]
}

run "rejects_non_sha_image_tag" {
  command = plan

  module {
    source = "./modules/ecs-service"
  }

  variables {
    # This is the exact value that was previously committed in
    # environments/lab/main.tf and should never pass validation.
    image_tag = "placeholder"
  }

  expect_failures = [
    var.image_tag,
  ]
}

run "accepts_short_sha_image_tag" {
  command = plan

  module {
    source = "./modules/ecs-service"
  }

  variables {
    image_tag = "abc1234"
  }

  assert {
    condition     = aws_ecs_task_definition.main.container_definitions != ""
    error_message = "Task definition should render container definitions for a valid short SHA."
  }
}

run "accepts_full_sha_image_tag" {
  command = plan

  module {
    source = "./modules/ecs-service"
  }

  variables {
    image_tag = "0123456789abcdef0123456789abcdef01234567"
  }
}

run "rejects_invalid_service_name" {
  command = plan

  module {
    source = "./modules/ecs-service"
  }

  variables {
    service_name = "x"
  }

  expect_failures = [
    var.service_name,
  ]
}

run "rejects_unapproved_owner" {
  command = plan

  module {
    source = "./modules/ecs-service"
  }

  variables {
    owner = "nobody"
  }

  expect_failures = [
    var.owner,
  ]
}

run "tasks_never_receive_a_public_ip" {
  command = plan

  module {
    source = "./modules/ecs-service"
  }

  assert {
    condition     = aws_ecs_service.main.network_configuration[0].assign_public_ip == false
    error_message = "Architecture rule violated: Fargate tasks must not receive a public IP."
  }
}

run "ecs_exec_is_enabled" {
  command = plan

  module {
    source = "./modules/ecs-service"
  }

  assert {
    condition     = aws_ecs_service.main.enable_execute_command == true
    error_message = "ECS Exec must be enabled (enable_execute_command = true) so runtime evidence can be collected."
  }
}

run "ecr_repository_is_immutable" {
  command = plan

  module {
    source = "./modules/ecs-service"
  }

  assert {
    condition     = aws_ecr_repository.main.image_tag_mutability == "IMMUTABLE"
    error_message = "ECR repository must use IMMUTABLE tag mutability to back the immutable-SHA guarantee."
  }
}
