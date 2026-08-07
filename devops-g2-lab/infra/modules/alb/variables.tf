variable "group_number" {
  type    = string
  default = "g2"
}

variable "vpc_id" {
  type = string
}

variable "public_subnet_ids" {
  type = list(string)
  validation {
    condition     = length(var.public_subnet_ids) >= 2
    error_message = "Architecture rule violated: ALB must span at least two public subnets/AZs."
  }
}

variable "app_port" {
  type    = number
  default = 3000
}

variable "owner" {
  type    = string
  default = "platform"
  validation {
    condition     = contains(["platform", "service-a", "service-b", "service-c", "release"], var.owner)
    error_message = "Architecture rule violated: Owner tag must be one of platform, service-a, service-b, service-c, release."
  }
}
