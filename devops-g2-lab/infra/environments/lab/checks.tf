check "traffic_contract" {
  assert {
    condition     = aws_security_group_rule.a_from_alb.source_security_group_id == module.alb.alb_sg_id
    error_message = "Traffic contract violation: ALB must be able to reach Service A."
  }

  assert {
    condition     = aws_security_group_rule.b_from_a.source_security_group_id == module.service_a.security_group_id
    error_message = "Traffic contract violation: Service A must be able to reach Service B."
  }

  assert {
    condition     = aws_security_group_rule.c_from_b.source_security_group_id == module.service_b.security_group_id
    error_message = "Traffic contract violation: Service B must be able to reach Service C."
  }

  assert {
    condition     = aws_security_group_rule.c_from_b.source_security_group_id != module.service_a.security_group_id
    error_message = "Traffic contract violation: Service A must not have direct ingress to Service C."
  }
}
