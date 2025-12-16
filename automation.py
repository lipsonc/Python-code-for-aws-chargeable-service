import boto3
from datetime import datetime, timedelta

region = "ap-south-1"  # change if needed

ec2 = boto3.client("ec2", region_name=region)
rds = boto3.client("rds", region_name=region)
elbv2 = boto3.client("elbv2", region_name=region)
ce = boto3.client("ce", region_name="us-east-1")  # Cost Explorer is global


def ec2_instances():
    running, stopped = [], []

    response = ec2.describe_instances()
    for r in response["Reservations"]:
        for i in r["Instances"]:
            state = i["State"]["Name"]
            instance_id = i["InstanceId"]

            if state == "running":
                running.append(instance_id)
            elif state == "stopped":
                stopped.append(instance_id)

    print("\n=== EC2 INSTANCES ===")
    print(f"Running: {running}")
    print(f"Stopped: {stopped}")


def elastic_ips():
    response = ec2.describe_addresses()

    print("\n=== ELASTIC IPs ===")
    for eip in response["Addresses"]:
        print({
            "PublicIP": eip.get("PublicIp"),
            "InUse": "InstanceId" in eip or "NetworkInterfaceId" in eip
        })


def nat_gateways():
    response = ec2.describe_nat_gateways()

    print("\n=== NAT GATEWAYS ===")
    for nat in response["NatGateways"]:
        print({
            "NatGatewayId": nat["NatGatewayId"],
            "State": nat["State"]
        })


def load_balancers():
    response = elbv2.describe_load_balancers()

    print("\n=== LOAD BALANCERS ===")
    for lb in response["LoadBalancers"]:
        print({
            "Name": lb["LoadBalancerName"],
            "Type": lb["Type"],
            "State": lb["State"]["Code"]
        })


def rds_instances():
    response = rds.describe_db_instances()

    print("\n=== RDS INSTANCES ===")
    for db in response["DBInstances"]:
        print({
            "DBIdentifier": db["DBInstanceIdentifier"],
            "Status": db["DBInstanceStatus"],
            "Engine": db["Engine"]
        })


def cost_by_service():
    end = datetime.utcnow().date()
    start = end - timedelta(days=7)

    response = ce.get_cost_and_usage(
        TimePeriod={
            "Start": start.strftime("%Y-%m-%d"),
            "End": end.strftime("%Y-%m-%d"),
        },
        Granularity="MONTHLY",
        Metrics=["UnblendedCost"],
        GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
    )

    print("\n=== COST (LAST 7 DAYS) ===")
    for group in response["ResultsByTime"][0]["Groups"]:
        cost = float(group["Metrics"]["UnblendedCost"]["Amount"])
        if cost > 0:
            print({
                "Service": group["Keys"][0],
                "CostUSD": round(cost, 2)
            })


if __name__ == "__main__":
    ec2_instances()
    elastic_ips()
    nat_gateways()
    load_balancers()
    rds_instances()
    cost_by_service()
