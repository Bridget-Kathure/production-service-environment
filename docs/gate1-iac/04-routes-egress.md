# 4. Route tables and egress — Group 2

## Choices (from kickoff)

- VPC `10.2.0.0/16`
- 2 public + 2 private subnets (`us-east-2a` / `us-east-2b`)
- Fargate in **private** subnets only; `assign_public_ip = false`
- Egress: **NAT Gateway per AZ** (two NAT Gateways, one per public subnet)

## Public route table

| Destination | Target |
|---|---|
| `10.2.0.0/16` | local |
| `0.0.0.0/0` | Internet Gateway |

## Private app route tables (one per AZ)

| Destination | Target |
|---|---|
| `10.2.0.0/16` | local |
| `0.0.0.0/0` | NAT Gateway (same AZ) |

## Placement

| Component | Subnet | Public IP |
|---|---|---|
| ALB | Public x2 AZs | ALB managed |
| NAT Gateway | Public, one per AZ (x2 total) | Elastic IP each |
| Fargate tasks A/B/C | Private x2 AZs | **None** |

## NAT vs endpoints

| | NAT per AZ (chosen) | Single NAT | VPC endpoints (not v1) |
|---|---|---|---|
| Upside | No single-AZ egress failure point | Lower cost (~$45/month) | Lowest idle cost |
| Downside | ~$90/month (2x NAT) | AZ dependency risk | More resources to wire |

Chosen: NAT per AZ, prioritizing reliability (Decision Card 1) over the ~$45/month saving from a single shared NAT.

Destroy both NAT Gateways + ALB with the workload each cycle; keep the bootstrap state bucket.
