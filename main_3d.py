#!/usr/bin/env python
"""
Panda3D 3D Graphics Launcher for Digital Organism Simulator
Запуск симулятора с красивой 3D визуализацией
"""

import sys
import os
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler('simulation_log.txt'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Main entry point for 3D simulator."""
    try:
        logger.info("=" * 60)
        logger.info("🌿 ЦИФРОВОЙ ОРГАНИЗМ - 3D СИМУЛЯТОР ЭВОЛЮЦИИ")
        logger.info("Digital Organism Evolution Simulator - 3D Version")
        logger.info("=" * 60)
        
        # Import after logging setup
        from simulation import Simulation
        from panda3d_engine import run_3d_simulator
        
        # Create simulation
        logger.info("🔬 Создание симуляции...")
        simulation = Simulation()
        logger.info(f"✅ Симуляция создана: {len(simulation.organisms)} организмов")
        
        # Start 3D renderer
        logger.info("🎮 Запуск 3D рендеринга...")
        logger.info("")
        logger.info("Управление:")
        logger.info("  Мышь: Вращение камеры")
        logger.info("  W/A/S/D: Движение камеры")
        logger.info("  Q/E: Вверх/Вниз")
        logger.info("  ESC: Выход")
        logger.info("")
        
        # Run simulator
        run_3d_simulator(simulation)
        
        logger.info("✅ Симуляция завершена")
        
    except ImportError as e:
        logger.error(f"❌ Ошибка импорта: {e}")
        logger.error("Убедитесь, что установлен Panda3D: pip install panda3d")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
