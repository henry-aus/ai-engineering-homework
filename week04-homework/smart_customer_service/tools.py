"""Tools for customer service operations."""
from typing import Dict, Any
from langchain_core.tools import tool


@tool
def query_order(order_id: str) -> Dict[str, Any]:
    """
    Query order status and logistics information.

    Args:
        order_id: The order ID to query

    Returns:
        Dictionary with order details including status and logistics
    """
    # Mock implementation - in production, this would call a real API
    mock_orders = {
        "ORD001": {
            "order_id": "ORD001",
            "status": "已发货",
            "create_time": "2026-03-24 10:30:00",
            "items": [
                {"name": "iPhone 15 Pro", "quantity": 1, "price": 7999.00}
            ],
            "total_amount": 7999.00,
            "logistics": {
                "company": "顺丰速运",
                "tracking_number": "SF1234567890",
                "current_location": "上海分拨中心",
                "estimated_delivery": "2026-03-27"
            }
        },
        "ORD002": {
            "order_id": "ORD002",
            "status": "配送中",
            "create_time": "2026-03-23 15:20:00",
            "items": [
                {"name": "MacBook Pro 14寸", "quantity": 1, "price": 15999.00}
            ],
            "total_amount": 15999.00,
            "logistics": {
                "company": "京东物流",
                "tracking_number": "JD9876543210",
                "current_location": "北京朝阳区配送站",
                "estimated_delivery": "2026-03-26"
            }
        },
        "ORD003": {
            "order_id": "ORD003",
            "status": "已签收",
            "create_time": "2026-03-20 09:15:00",
            "items": [
                {"name": "AirPods Pro", "quantity": 2, "price": 1999.00}
            ],
            "total_amount": 3998.00,
            "logistics": {
                "company": "顺丰速运",
                "tracking_number": "SF0987654321",
                "current_location": "已签收",
                "delivery_time": "2026-03-22 14:30:00"
            }
        }
    }

    if order_id in mock_orders:
        return mock_orders[order_id]
    else:
        return {
            "error": "订单不存在",
            "message": f"未找到订单号: {order_id}",
            "order_id": order_id
        }


@tool
def process_refund(order_id: str, reason: str = "") -> Dict[str, Any]:
    """
    Process refund request for an order.

    Args:
        order_id: The order ID to refund
        reason: Reason for refund (optional)

    Returns:
        Dictionary with refund processing result
    """
    # Mock implementation
    mock_orders = {
        "ORD001": {"status": "已发货", "amount": 7999.00},
        "ORD002": {"status": "配送中", "amount": 15999.00},
        "ORD003": {"status": "已签收", "amount": 3998.00}
    }

    if order_id not in mock_orders:
        return {
            "success": False,
            "error": "订单不存在",
            "message": f"未找到订单号: {order_id}"
        }

    order = mock_orders[order_id]

    # Check if order is eligible for refund
    if order["status"] in ["已签收", "已发货"]:
        return {
            "success": True,
            "order_id": order_id,
            "refund_amount": order["amount"],
            "refund_id": f"REF{order_id[3:]}",
            "status": "退款处理中",
            "estimated_time": "3-5个工作日",
            "message": f"退款申请已提交，退款金额: ¥{order['amount']:.2f}",
            "reason": reason if reason else "未提供原因"
        }
    else:
        return {
            "success": False,
            "error": "订单状态不支持退款",
            "message": f"订单状态为'{order['status']}'，暂不支持退款"
        }


@tool
def issue_invoice(order_id: str, invoice_type: str = "个人", invoice_title: str = "") -> Dict[str, Any]:
    """
    Issue invoice for an order.

    Args:
        order_id: The order ID to issue invoice for
        invoice_type: Type of invoice (个人/企业)
        invoice_title: Invoice title (required for 企业 type)

    Returns:
        Dictionary with invoice issuing result
    """
    # Mock implementation
    mock_orders = {
        "ORD001": {"amount": 7999.00, "status": "已发货"},
        "ORD002": {"amount": 15999.00, "status": "配送中"},
        "ORD003": {"amount": 3998.00, "status": "已签收"}
    }

    if order_id not in mock_orders:
        return {
            "success": False,
            "error": "订单不存在",
            "message": f"未找到订单号: {order_id}"
        }

    order = mock_orders[order_id]

    if invoice_type == "企业" and not invoice_title:
        return {
            "success": False,
            "error": "缺少必要信息",
            "message": "企业发票需要提供发票抬头"
        }

    return {
        "success": True,
        "order_id": order_id,
        "invoice_id": f"INV{order_id[3:]}",
        "invoice_type": invoice_type,
        "invoice_title": invoice_title if invoice_title else "个人",
        "amount": order["amount"],
        "status": "已开具",
        "message": f"发票已开具，发票号: INV{order_id[3:]}",
        "download_url": f"https://example.com/invoice/INV{order_id[3:]}.pdf"
    }


# List of all available tools
TOOLS = [query_order, process_refund, issue_invoice]
