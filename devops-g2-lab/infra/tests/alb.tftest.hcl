# Native Terraform tests for modules/alb. Mocked provider - no AWS
# credentials or account required.
#
# Run with:  terraform test tests/alb.tftest.hcl

mock_provider "aws" {}

variables {
  vpc_id            = "vpc-mock00000000"
  public_subnet_ids = ["subnet-pub-az1", "subnet-pub-az2"]
  app_port          = 3000
  owner             = "platform"
}

run "rejects_single_az" {
  command = plan

  module {
    source = "./modules/alb"
  }

  variables {
    public_subnet_ids = ["subnet-pub-az1"]
  }

  expect_failures = [
    var.public_subnet_ids,
  ]
}

run "accepts_two_azs" {
  command = plan

  module {
    source = "./modules/alb"
  }

  assert {
    condition     = length(var.public_subnet_ids) >= 2
    error_message = "ALB must span at least two public subnets/AZs."
  }
}

run "target_group_uses_ip_targets" {
  command = plan

  module {
    source = "./modules/alb"
  }

  assert {
    condition     = aws_lb_target_group.service_a.target_type == "ip"
    error_message = "Architecture rule violated: target group type must be 'ip' for Fargate awsvpc mode."
  }
}

run "alb_is_internet_facing_on_port_80" {
  command = plan

  module {
    source = "./modules/alb"
  }

  assert {
    condition     = aws_lb.main.internal == false
    error_message = "ALB must be internet-facing to satisfy the Internet -> ALB traffic contract."
  }

  assert {
    condition     = aws_lb_listener.http.port == 80
    error_message = "ALB listener must be on port 80 per the traffic contract."
  }
}
