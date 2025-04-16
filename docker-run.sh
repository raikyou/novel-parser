#!/bin/bash

# Default values
PORT=5000
NOVEL_DIR="$(pwd)/docs"
DATA_DIR="$(pwd)/data"
LOGS_DIR="$(pwd)/logs"
CONTAINER_NAME="novel-parser"
IMAGE_NAME="ghcr.io/yourusername/novel-parser:latest"

# Help message
show_help() {
    echo "Usage: $0 [OPTIONS]"
    echo "Run the Novel Parser in a Docker container."
    echo ""
    echo "Options:"
    echo "  -p, --port PORT        Port to expose (default: 5000)"
    echo "  -d, --dir DIRECTORY    Directory containing novel files (default: ./docs)"
    echo "  --data DIRECTORY       Directory for database (default: ./data)"
    echo "  --logs DIRECTORY       Directory for logs (default: ./logs)"
    echo "  -n, --name NAME        Container name (default: novel-parser)"
    echo "  -i, --image IMAGE      Docker image (default: ghcr.io/yourusername/novel-parser:latest)"
    echo "  -h, --help             Show this help message"
    exit 0
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -p|--port)
            PORT="$2"
            shift 2
            ;;
        -d|--dir)
            NOVEL_DIR="$2"
            shift 2
            ;;
        --data)
            DATA_DIR="$2"
            shift 2
            ;;
        -n|--name)
            CONTAINER_NAME="$2"
            shift 2
            ;;
        -i|--image)
            IMAGE_NAME="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            ;;
    esac
done

# Check if container already exists
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "Container ${CONTAINER_NAME} already exists. Stopping and removing..."
    docker stop ${CONTAINER_NAME} > /dev/null
    docker rm ${CONTAINER_NAME} > /dev/null
fi

# Create data directory if it doesn't exist
mkdir -p "${DATA_DIR}"

# Run the container
echo "Starting Novel Parser container..."
echo "Novel directory: ${NOVEL_DIR}"
echo "Data directory: ${DATA_DIR}"
echo "Port: ${PORT}"

docker run -d \
    --name ${CONTAINER_NAME} \
    -p ${PORT}:5000 \
    -v "${NOVEL_DIR}:/app/docs" \
    -v "${DATA_DIR}:/app/data" \
    ${IMAGE_NAME}

echo "Container started. Access the API at http://localhost:${PORT}"
