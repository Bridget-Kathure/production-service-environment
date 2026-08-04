variable "service_name" {
  description = "Name of the service (a, b, or c)"
  type        = string
  validation {
    condition     = contains(["a", "b", "c"], var.service_name)
    error_message = "Service name must be a, b, or c."
  }
}

variable "group_number" {
  type    = string
  default = "g2"
}

variable "cluster_arn" {
  type = string
}

variable "vpc_id" {
  type = string
}

variable "private_subnet_ids" {
  type = list(string)
}

variable "execution_role_arn" {
  type = string
}

variable "task_role_arn" {
  type = string
}

variable "image_tag" {
  description = "Git SHA tag for the container image"
  type        = string
  validation {
    condition     = var.image_tag != "latest"
    error_message = "Image tag cannot be 'latest'. Use a Git SHA."
  }
}

variable "app_port" {
  type    = number
  default = 3000
}

variable "desired_count" {
  type    = number
  default = 1
}

variable "cpu" {
  type    = string
  default = "256"
}

variable "memory" {
  type    = string
  default = "512"
}

variable "alb_target_group_arn" {
  type    = string
  default = ""
}

variable "namespace_id" {
  type = string
}

variable "namespace_name" {
  type = string
}

variable "upstream_service" {
  type    = string
  default = ""
}

variable "ingress_sg_id" {
  type    = string
  default = ""
}

variable "owner" {
  type    = string
  default = "platform"
}
