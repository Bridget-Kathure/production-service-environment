output "service_name" {
  value = aws_ecs_service.main.name
}

output "security_group_id" {
  value = aws_security_group.main.id
}

output "ecr_repository_url" {
  value = aws_ecr_repository.main.repository_url
}

output "cloudwatch_log_group" {
  value = aws_cloudwatch_log_group.main.name
}
