variable "group_number" {
  type    = string
  default = "g2"
}

variable "vpc_cidr" {
  type    = string
  default = "10.2.0.0/16"
}

variable "availability_zones" {
  type    = list(string)
  default = ["us-east-2a", "us-east-2b"]
}

variable "public_subnet_cidrs" {
  type    = list(string)
  default = ["10.2.0.0/20", "10.2.16.0/20"]
}

variable "private_app_subnet_cidrs" {
  type    = list(string)
  default = ["10.2.32.0/19", "10.2.64.0/19"]
}

variable "owner" {
  type    = string
  default = "platform"
  validation {
    condition     = contains(["platform", "service-a", "service-b", "service-c", "release"], var.owner)
    error_message = "Architecture rule violated: Owner tag must be one of platform, service-a, service-b, service-c, release."
  }
}
