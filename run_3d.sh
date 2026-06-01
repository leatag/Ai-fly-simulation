#!/bin/bash
# Quick launcher for 3D Simulator

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Creating..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -q pygame numpy panda3d
else
    source venv/bin/activate
fi

echo ""
echo "╔═══════════════════════════════════════════════════════╗"
echo "║  🌿 ЦИФРОВОЙ ОРГАНИЗМ - 3D СИМУЛЯТОР ЭВОЛЮЦИИ      ║"
echo "║      Digital Organism Evolution Simulator 3D        ║"
echo "╚═══════════════════════════════════════════════════════╝"
echo ""
echo "🎮 Запуск 3D симулятора..."
echo ""

# Run the simulator
python main_3d.py

echo ""
echo "✅ Симулятор завершился"
