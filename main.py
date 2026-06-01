"""
Main entry point for the Digital Organism Simulator.
Initializes pygame, the simulation, renderer, and UI, and runs the main loop.

Цифровой организм — главный модуль запуска симуляции.
"""

import sys
import time
import pygame

from simulation import Simulation
from renderer import Renderer
from ui import UIManager
from config import LOG_FILE, TICK_RATES


def main() -> None:
    """
    Main entry point. Initializes all components and runs the game loop.
    """
    print("=" * 60)
    print("   ЦИФРОВОЙ ОРГАНИЗМ — СИМУЛЯТОР ЭВОЛЮЦИИ")
    print("   Digital Organism Evolution Simulator v1.0")
    print("=" * 60)
    print()
    print("Управление:")
    print("  Пробел         - Пауза")
    print("  +/-            - Ускорение/замедление")
    print("  Стрелки        - Движение камеры")
    print("  Мышь (клик)    - Выбор существа")
    print("  ESC            - Отмена выбора")
    print()
    print(f"Лог сохраняется в: {LOG_FILE}")
    print()

    # Initialize components
    simulation = Simulation()
    renderer = Renderer()
    ui_manager = UIManager()

    # Performance tracking
    tick_accumulator = 0.0
    last_time = time.time()
    running = True

    # Main loop
    while running:
        current_time = time.time()
        delta_time = current_time - last_time
        last_time = current_time

        # Handle pygame events
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    # ESC to quit if no organism selected
                    if ui_manager.selected_organism is None:
                        running = False

        # Handle UI events
        ui_result = ui_manager.handle_events(
            events, simulation.world,
            simulation.organisms, renderer
        )

        # Apply UI actions
        if ui_result["pause_toggle"]:
            simulation.set_paused(ui_manager.is_paused)

        if ui_result["speed_up"] or ui_result["speed_down"]:
            tick_rate = ui_manager.get_tick_rate()
            simulation.set_tick_rate(tick_rate)

        if ui_result["select_organism"] is not None:
            simulation.select_organism(ui_result["select_organism"])

        # Camera movement
        dx, dy = ui_result["camera_move"]
        if dx != 0 or dy != 0:
            renderer.camera.move(dx, dy)

        # Update simulation with tick rate limiting
        tick_rate = simulation.tick_rate
        tick_interval = 1.0 / tick_rate if tick_rate > 0 else 0.0

        tick_accumulator += delta_time

        # Run simulation ticks based on accumulated time
        ticks_processed = 0
        max_ticks_per_frame = 5  # prevent spiral of death

        while tick_accumulator >= tick_interval and ticks_processed < max_ticks_per_frame:
            simulation.update()
            tick_accumulator -= tick_interval
            ticks_processed += 1

            # If paused, break out immediately
            if simulation.is_paused:
                tick_accumulator = 0
                break

        # Add log lines from simulation events
        for event in simulation.evolution_tracker.get_recent_events(5):
            if event not in ui_manager.log_lines:
                ui_manager.add_log_line(event)

        # Render everything
        renderer.render(
            simulation.world,
            simulation.organisms,
            ui_manager
        )

        # Cap the render loop to ~60 FPS
        renderer.clock.tick(60)

    # Cleanup
    print("Завершение симуляции...")
    simulation.cleanup()
    renderer.cleanup()
    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()