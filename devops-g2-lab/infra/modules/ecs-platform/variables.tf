variable "group_number" {
  type    = string
  default = "g2"
}

variable "vpc_id" {
  type = string
}

variable "owner" {
  type    = string
  default = "platform"
  validation {
    condition     = contains(["platform", "service-a", "service-b", "service-c", "release"], var.owner)
    error_message = "Architecture rule violated: Owner tag must be one of platform, service-a, service-b, service-c, release."
  }
}
