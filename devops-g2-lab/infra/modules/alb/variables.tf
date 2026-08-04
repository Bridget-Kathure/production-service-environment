variable "group_number" {
  type    = string
  default = "g2"
}

variable "vpc_id" {
  type = string
}

variable "public_subnet_ids" {
  type = list(string)
}

variable "app_port" {
  type    = number
  default = 3000
}

variable "owner" {
  type    = string
  default = "platform"
}
