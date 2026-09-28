#!/bin/bash
# Unorouter Pricing API Launch Script

set -e

PROJECT_DIR="/home/coding_hizer/fun/proj/Unorouter_GLMtracker_api"
PID_FILE="$PROJECT_DIR/tmp/unorouter_api.pid"
LOG_FILE="$PROJECT_DIR/tmp/unorouter_api.log"

cd "$PROJECT_DIR"

start() {
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        echo "Server already running (PID: $(cat "$PID_FILE"))"
        exit 1
    fi
    
    echo "Starting Unorouter Pricing API on port 7414..."
    nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 7414 > "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"
    sleep 2
    
    if curl -s http://localhost:7414/health > /dev/null; then
        echo "Server started successfully (PID: $(cat "$PID_FILE"))"
        echo "Accessible from Windows at: http://localhost:7414"
        echo "Logs: $LOG_FILE"
    else
        echo "Failed to start server. Check logs: $LOG_FILE"
        rm -f "$PID_FILE"
        exit 1
    fi
}

stop() {
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        echo "Stopping server (PID: $(cat "$PID_FILE"))..."
        kill "$(cat "$PID_FILE")"
        rm -f "$PID_FILE"
        echo "Server stopped"
    else
        echo "Server not running"
    fi
}

restart() {
    stop
    sleep 1
    start
}

status() {
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        echo "Server is running (PID: $(cat "$PID_FILE"))"
        curl -s http://localhost:7414/health | python3 -m json.tool
    else
        echo "Server is not running"
    fi
}

logs() {
    if [ -f "$LOG_FILE" ]; then
        tail -f "$LOG_FILE"
    else
        echo "No log file found"
    fi
}

test() {
    echo "Testing endpoints..."
    echo "=== Health ==="
    curl -s http://localhost:7414/health | python3 -m json.tool
    echo ""
    echo "=== Catalog (first 3 models) ==="
    curl -s http://localhost:7414/pricing/catalog | python3 -c "import sys, json; data=json.load(sys.stdin); print(json.dumps(data[:3], indent=2))"
    echo ""
    echo "=== GLM 5.3 Pricing ==="
    curl -s http://localhost:7414/pricing/catalog/glm-5.3 | python3 -m json.tool
    echo ""
    echo "=== Counts ==="
    curl -s http://localhost:7414/pricing/counts | python3 -m json.tool
    echo ""
    echo "=== Vendors (first 10) ==="
    curl -s http://localhost:7414/pricing/vendors | python3 -c "import sys, json; data=json.load(sys.stdin); print('vendor_names:', data['vendor_names'][:10])"
}

case "$1" in
    start)   start ;;
    stop)    stop ;;
    restart) restart ;;
    status)  status ;;
    logs)    logs ;;
    test)    test ;;
    *)       echo "Usage: $0 {start|stop|restart|status|logs|test}" ;;
esac