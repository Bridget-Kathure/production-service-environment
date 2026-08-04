output "cluster_arn" {
  value = aws_ecs_cluster.main.arn
}

output "cluster_name" {
  value = aws_ecs_cluster.main.name
}

output "namespace_id" {
  value = aws_service_discovery_private_dns_namespace.main.id
}

output "namespace_arn" {
  value = aws_service_discovery_private_dns_namespace.main.arn
}

output "namespace_name" {
  value = aws_service_discovery_private_dns_namespace.main.name
}

output "log_group_name" {
  value = aws_cloudwatch_log_group.ecs.name
}

output "execution_role_arn" {
  value = aws_iam_role.ecs_execution.arn
}

output "task_role_arn" {
  value = aws_iam_role.ecs_task.arn
}
