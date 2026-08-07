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
    # Accepts a 7-char short SHA or a full 40-char SHA (matches what the
    # buildspecs produce: cut -c1-7 of CODEBUILD_RESOLVED_SOURCE_VERSION).
    # Explicitly rejects "latest" and placeholder values like "placeholder".
    condition     = can(regex("^[0-9a-f]{7}$|^[0-9a-f]{40}$", var.image_tag))
    error_message = "Image tag must be an immutable Git SHA (7 or 40 lowercase hex characters). 'latest' and placeholder values are not accepted."
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

variable "upstream_port" {
  description = "Port the upstream service listens on, for calls made via Service Connect (empty when this service has no upstream, e.g. Service C)"
  type        = string
  default     = ""
}

variable "ingress_sg_id" {
  type    = string
  default = ""
}

variable "owner" {
  type    = string
  default = "platform"
  validation {
    condition     = contains(["platform", "service-a", "service-b", "service-c", "release"], var.owner)
    error_message = "Architecture rule violated: Owner tag must be one of platform, service-a, service-b, service-c, release."
  }
}
