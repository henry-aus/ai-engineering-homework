#!/bin/bash

# Docker Compose Services Management Script

case "$1" in
  start)
    echo "Starting Milvus and Neo4j services..."
    docker-compose up -d
    echo ""
    echo "Services starting up..."
    echo "- Milvus: http://localhost:19530"
    echo "- Milvus MinIO Console: http://localhost:9001 (minioadmin/minioadmin)"
    echo "- Neo4j Browser: http://localhost:7474 (neo4j/password123)"
    echo ""
    echo "Waiting for services to be healthy..."
    sleep 10
    docker-compose ps
    ;;

  stop)
    echo "Stopping services..."
    docker-compose down
    ;;

  restart)
    echo "Restarting services..."
    docker-compose restart
    ;;

  logs)
    if [ -z "$2" ]; then
      docker-compose logs -f
    else
      docker-compose logs -f "$2"
    fi
    ;;

  status)
    docker-compose ps
    ;;

  clean)
    echo "⚠️  WARNING: This will remove all containers and data!"
    read -p "Are you sure? (yes/no): " confirm
    if [ "$confirm" = "yes" ]; then
      docker-compose down -v
      rm -rf data/
      echo "All data cleaned."
    else
      echo "Cancelled."
    fi
    ;;

  *)
    echo "Usage: $0 {start|stop|restart|logs|status|clean}"
    echo ""
    echo "Commands:"
    echo "  start   - Start all services"
    echo "  stop    - Stop all services"
    echo "  restart - Restart all services"
    echo "  logs    - View logs (optional: specify service name)"
    echo "  status  - Show service status"
    echo "  clean   - Remove all containers and data"
    echo ""
    echo "Examples:"
    echo "  $0 start"
    echo "  $0 logs milvus"
    echo "  $0 status"
    exit 1
    ;;
esac
