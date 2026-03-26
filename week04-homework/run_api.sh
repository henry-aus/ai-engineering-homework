#!/bin/bash
# Quick script to start the API server

echo "=================================================="
echo "Starting Smart Customer Service API Server"
echo "=================================================="
echo ""
echo "API Documentation: http://localhost:8000/docs"
echo "Health Check:      http://localhost:8000/health"
echo ""
echo "Press Ctrl+C to stop the server"
echo "=================================================="
echo ""

python -m smart_customer_service.api
