"""
Panda3D 3D Graphics Engine for Digital Organism Simulator
Реалистичная 3D визуализация эволюции организмов

Beautiful 3D rendering with realistic models, lighting, and camera control.
"""

import math
import os
import sys
import numpy as np
from panda3d.core import *
from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from direct.gui.OnscreenText import OnscreenText
from direct.gui.OnscreenImage import OnscreenImage
from config import WORLD_WIDTH, WORLD_HEIGHT, WORLD_SIZE, DISPLAY_WIDTH, DISPLAY_HEIGHT


class OrganismModel3D:
    """3D model of an organism."""
    
    def __init__(self, parent_node, organism_id: int, x: float, y: float):
        self.organism_id = organism_id
        self.x = x
        self.y = y
        
        # Create main body group
        self.node = parent_node.attachNewNode(f"organism_{organism_id}")
        self.node.setPos(x - WORLD_WIDTH / 2, 0.5, y - WORLD_HEIGHT / 2)
        
        # Main body (soft rounded sphere)
        body = loader.loadModel("models/misc/sphere")
        body.setScale(0.18)
        body.reparentTo(self.node)
        body_color = [(0.35, 0.18, 0.12), (0.18, 0.35, 0.25), (0.35, 0.18, 0.3)][organism_id % 3]
        body_material = Material()
        body_material.setDiffuse((body_color[0], body_color[1], body_color[2], 1.0))
        body_material.setSpecular((0.45, 0.45, 0.45, 1.0))
        body_material.setShininess(24.0)
        body.setMaterial(body_material)
        
        # Head (small sphere)
        head = loader.loadModel("models/misc/sphere")
        head.setScale(0.1)
        head.setPos(0, 0.27, 0.08)
        head.reparentTo(self.node)
        head_material = Material()
        head_material.setDiffuse((body_color[0] + 0.08, body_color[1] + 0.05, body_color[2] + 0.05, 1.0))
        head_material.setSpecular((0.55, 0.55, 0.55, 1.0))
        head_material.setShininess(30.0)
        head.setMaterial(head_material)
        
        # Eyes (red spheres)
        left_eye = loader.loadModel("models/misc/sphere")
        left_eye.setScale(0.05)
        left_eye.setPos(-0.08, 0.32, 0.05)
        left_eye.reparentTo(self.node)
        eye_material = Material()
        eye_material.setDiffuse((1.0, 0.0, 0.0, 1.0))  # Red
        eye_material.setSpecular((1.0, 1.0, 1.0, 1.0))
        left_eye.setMaterial(eye_material)
        
        right_eye = loader.loadModel("models/misc/sphere")
        right_eye.setScale(0.05)
        right_eye.setPos(0.08, 0.32, 0.05)
        right_eye.reparentTo(self.node)
        right_eye.setMaterial(eye_material)
        
        # Antennae
        for i, x_offset in enumerate([-0.06, 0.06]):
            antenna = loader.loadModel("models/box")
            antenna.setScale(0.02, 0.08, 0.02)
            antenna.setPos(x_offset, 0.35, 0.05)
            antenna.reparentTo(self.node)
            antenna_material = Material()
            antenna_material.setDiffuse((0.2, 0.2, 0.2, 1.0))  # Gray
            antenna.setMaterial(antenna_material)
        
        # Legs (6 boxes)
        leg_positions = [
            (-0.1, 0.1, -0.08),
            (-0.1, 0.1, 0.08),
            (-0.1, -0.05, -0.08),
            (-0.1, -0.05, 0.08),
            (0.1, 0.1, -0.08),
            (0.1, 0.1, 0.08),
        ]
        
        for leg_pos in leg_positions:
            leg = loader.loadModel("models/box")
            leg.setScale(0.02, 0.15, 0.02)
            leg.setPos(leg_pos)
            leg.reparentTo(self.node)
            leg_material = Material()
            leg_material.setDiffuse((0.25, 0.15, 0.05, 1.0))  # Light brown
            leg.setMaterial(leg_material)
        
        # Wings
        for x_offset in [-0.12, 0.12]:
            wing = loader.loadModel("models/box")
            wing.setScale(0.08, 0.2, 0.01)
            wing.setPos(x_offset, 0.05, 0)
            wing.reparentTo(self.node)
            wing_material = Material()
            wing_material.setDiffuse((0.8, 0.8, 0.8, 0.5))  # Transparent gray
            wing.setMaterial(wing_material)
        
        self.wings = [self.node.getChild(i) for i in range(self.node.getNumChildren()-2, self.node.getNumChildren())]
        self.wing_rotation = 0
        self.hover_phase = np.random.uniform(0.0, 2.0 * math.pi)
        self.color_index = organism_id % 3
    
    def update(self, x: float, y: float, animation_frame: int = 0, emotion: str = "normal"):
        """Update organism position and animation."""
        self.x = x
        self.y = y
        self.hover_phase += 0.08
        hover_x = math.cos(self.hover_phase) * 0.08
        hover_z = math.sin(self.hover_phase) * 0.08
        self.node.setPos(
            x - WORLD_WIDTH / 2 + hover_x,
            0.5 + math.sin(animation_frame * 0.3) * 0.05,
            y - WORLD_HEIGHT / 2 + hover_z
        )
        
        # Animate wings
        self.wing_rotation += 20
        for wing in self.wings:
            wing.setR(self.wing_rotation % 360)
        
        # Update color based on emotion
        emotion_colors = {
            "normal": (0.3, 0.1, 0.1),
            "searching": (0.5, 0.2, 0.1),
            "scared": (0.2, 0.0, 0.0),
            "happy": (0.4, 0.3, 0.1),
        }
        
        color = emotion_colors.get(emotion, (0.3, 0.1, 0.1))
        body = self.node.getChild(0)
        material = Material()
        material.setDiffuse((color[0], color[1], color[2], 1.0))
        material.setSpecular((0.5, 0.5, 0.5, 1.0))
        body.setMaterial(material)
    
    def remove(self):
        """Remove the model."""
        self.node.removeNode()


class Terrain3D:
    """3D terrain and environment."""
    
    def __init__(self, parent_node):
        self.parent = parent_node
        self.create_terrain()
        self.create_trees()
        self.create_sky()
    
    def create_terrain(self):
        """Create grass terrain."""
        ground_card = CardMaker("ground")
        ground_card.setFrame(-WORLD_WIDTH / 2, WORLD_WIDTH / 2, -WORLD_HEIGHT / 2, WORLD_HEIGHT / 2)
        ground = self.parent.attachNewNode(ground_card.generate())
        ground.setPos(0, 0, 0)
        ground.setP(-90)
        ground.setTwoSided(True)
        ground.reparentTo(self.parent)
        
        ground_tex = None
        if os.path.exists("maps/envir-ground.jpg"):
            ground_tex = loader.loadTexture("maps/envir-ground.jpg")

        if ground_tex:
            ground.setTexture(ground_tex)
            ground.setTexScale(TextureStage.getDefault(), WORLD_WIDTH / 8, WORLD_HEIGHT / 8)
        else:
            ground_material = Material()
            ground_material.setDiffuse((0.2, 0.65, 0.15, 1.0))
            ground_material.setSpecular((0.1, 0.1, 0.1, 1.0))
            ground.setMaterial(ground_material)
        
        # Add shallow water around the edges for a richer scene
        water_card = CardMaker("water")
        water_card.setFrame(-WORLD_WIDTH, WORLD_WIDTH, -WORLD_HEIGHT, WORLD_HEIGHT)
        water = self.parent.attachNewNode(water_card.generate())
        water.setZ(-0.08)
        water.setP(-90)
        water.setColor(0.1, 0.35, 0.55, 0.75)
        water.setTransparency(TransparencyAttrib.MAlpha)
        water.setDepthWrite(False)
        water.reparentTo(self.parent)
        self.water_stage = TextureStage("water")
        water_tex = None
        if os.path.exists("maps/water.png"):
            water_tex = loader.loadTexture("maps/water.png")

        if water_tex:
            water.setTexture(self.water_stage, water_tex)
            water.setTexScale(self.water_stage, WORLD_WIDTH / 6, WORLD_HEIGHT / 6)
        else:
            water_tex = self._generate_water_texture(256, 256)
            water.setTexture(self.water_stage, water_tex)
            water.setTexScale(self.water_stage, WORLD_WIDTH / 6, WORLD_HEIGHT / 6)
        self.water = water
        self.water.setTexGen(self.water_stage, TexGenAttrib.MWorldPosition)
        self.water.setTexOffset(self.water_stage, 0, 0)

        # World boundary walls
        wall_thickness = 0.4
        wall_height = 2.0
        boundary_color = (0.08, 0.06, 0.04, 1.0)
        boundaries = [
            (0, -WORLD_HEIGHT / 2, WORLD_WIDTH, wall_thickness),
            (0, WORLD_HEIGHT / 2, WORLD_WIDTH, wall_thickness),
            (-WORLD_WIDTH / 2, 0, wall_thickness, WORLD_HEIGHT),
            (WORLD_WIDTH / 2, 0, wall_thickness, WORLD_HEIGHT),
        ]
        for x, z, width, depth in boundaries:
            wall = loader.loadModel("models/box")
            wall.setScale(width / 2, wall_height / 2, depth / 2)
            wall.setPos(x, wall_height / 2, z)
            wall.setColor(boundary_color)
            wall.reparentTo(self.parent)

        # Add a few decorative grass clumps
        for i in range(8):
            patch = loader.loadModel("models/misc/sphere")
            patch.setScale(1.2, 0.1, 1.2)
            patch.setPos(
                np.random.uniform(-WORLD_WIDTH / 2 + 5, WORLD_WIDTH / 2 - 5),
                0.01,
                np.random.uniform(-WORLD_HEIGHT / 2 + 5, WORLD_HEIGHT / 2 - 5)
            )
            patch.setColor(0.15, 0.5 + np.random.rand() * 0.25, 0.1, 1.0)
            patch.setTransparency(TransparencyAttrib.MAlpha)
            patch.reparentTo(self.parent)
    
    def create_trees(self):
        """Create trees."""
        tree_positions = [
            (-15, 5),
            (15, 5),
            (-15, -15),
            (15, -15),
            (5, -25),
            (-5, 25),
        ]
        
        for x, z in tree_positions:
            self.create_tree(x, z)
    
    def create_tree(self, x: float, z: float):
        """Create a single tree."""
        # Trunk
        trunk = loader.loadModel("models/box")
        trunk.setScale(0.5, 3, 0.5)
        trunk.setPos(x, 1.5, z)
        trunk.reparentTo(self.parent)
        trunk.setColor(0.45, 0.25, 0.08, 1.0)
        
        canopy = loader.loadModel("models/misc/sphere")
        canopy.setScale(3.5)
        canopy.setPos(x, 5, z)
        canopy.reparentTo(self.parent)
        
        canopy_material = Material()
        canopy_material.setDiffuse((0.12, 0.55, 0.12, 1.0))  # Dark green
        canopy_material.setSpecular((0.3, 0.35, 0.3, 1.0))
        canopy.setMaterial(canopy_material)
    
    def create_sky(self):
        """Create skybox with clouds."""
        sky = loader.loadModel("models/box")
        sky.setScale(-220)
        sky.setTwoSided(True)
        sky.setBin("background", 0)
        sky.setDepthWrite(False)
        sky.setLightOff()
        sky.setCompass()
        sky.reparentTo(self.parent)

        sky_tex = None
        sky_tex = None
        if os.path.exists("maps/sky.jpg"):
            sky_tex = loader.loadTexture("maps/sky.jpg")

        if not sky_tex:
            sky_tex = self._generate_sky_texture(1024, 512)
        sky.setTexture(sky_tex, 1)
        sky.setTexScale(TextureStage.getDefault(), 2, 2)

    def animate_water(self, task):
        if hasattr(self, 'water') and hasattr(self, 'water_stage'):
            t = globalClock.getFrameTime()
            self.water.setTexOffset(self.water_stage, t * 0.02, t * 0.03)
        return Task.cont

    def _generate_sky_texture(self, width: int = 512, height: int = 256):
        img = PNMImage(width, height, 3)
        for y in range(height):
            t = y / max(1, height - 1)
            r = 0.55 + 0.2 * (1 - t)
            g = 0.72 + 0.18 * (1 - t)
            b = 0.92 + 0.08 * (1 - t)
            for x in range(width):
                img.setXel(x, y, r, g, b)

        for _ in range(30):
            cx = np.random.uniform(0, width)
            cy = np.random.uniform(height * 0.4, height * 0.95)
            radius = np.random.uniform(40, 90)
            for dy in range(int(-radius), int(radius)):
                y0 = int(cy + dy)
                if y0 < 0 or y0 >= height:
                    continue
                x_radius = math.sqrt(max(0.0, radius ** 2 - dy ** 2))
                start = int(max(0, cx - x_radius))
                end = int(min(width, cx + x_radius))
                alpha = 0.18 * (1 - abs(dy) / radius)
                for x0 in range(start, end):
                    old_r, old_g, old_b = img.getXel(x0, y0)
                    img.setXel(x0, y0,
                               min(1.0, old_r + alpha * 1.0),
                               min(1.0, old_g + alpha * 1.0),
                               min(1.0, old_b + alpha * 1.0))

        tex = Texture("sky_clouds")
        tex.load(img)
        return tex

    def _generate_water_texture(self, width: int = 256, height: int = 256):
        img = PNMImage(width, height, 3)
        for y in range(height):
            y_norm = y / max(1, height - 1)
            for x in range(width):
                x_norm = x / max(1, width - 1)
                wave = 0.1 * math.sin(2 * math.pi * (x_norm * 8 + y_norm * 4))
                ripple = 0.05 * math.sin(2 * math.pi * (x_norm * 16 + y_norm * 6))
                r = min(1.0, 0.05 + 0.25 * y_norm + wave + ripple)
                g = min(1.0, 0.15 + 0.2 * y_norm + wave * 0.5 + ripple * 0.4)
                b = min(1.0, 0.3 + 0.35 * y_norm + wave * 1.2 + ripple)
                img.setXel(x, y, r, g, b)
        tex = Texture("water_pattern")
        tex.setWrapU(Texture.WMRepeat)
        tex.setWrapV(Texture.WMRepeat)
        tex.load(img)
        return tex


class Panda3DSimulator(ShowBase):
    """Main 3D simulator using Panda3D."""
    
    def __init__(self):
        ShowBase.__init__(self)
        
        # Window setup
        self.win.setClearColor(Vec4(0.7, 0.85, 1.0, 1.0))  # Sky blue
        self.setFrameRateMeter(True)
        self.disableMouse()
        self.accept("escape", self.userExit)
        self.accept("window-event", self.handle_window_event)
        
        # Camera setup
        self.camera.setPos(0, 20, 30)
        self.camera.lookAt(0, 5, 0)
        
        # Lighting
        self.setup_lighting()
        self.render.setShaderAuto()
        
        # Create 3D environment
        self.environment_node = self.render.attachNewNode("environment")
        self.terrain = Terrain3D(self.environment_node)
        self.taskMgr.add(self.terrain.animate_water, "water_animate")
        
        # Organism models
        self.organisms_node = self.render.attachNewNode("organisms")
        self.organism_models = {}
        
        # Simulation reference
        self.simulation = None
        self.frame_count = 0
        
        # UI
        self.setup_ui()
        
        # Camera controls
        self.camera_speed = 20.0
        self.mouse_sensitivity = 0.22
        self.camera_pitch = -25.0
        self.camera_yaw = 0.0
        self.center_x = int(DISPLAY_WIDTH / 2)
        self.center_y = int(DISPLAY_HEIGHT / 2)
        self.win.movePointer(0, self.center_x, self.center_y)
        self.taskMgr.add(self.update_camera_task, "camera_update")
        
        # Simulation update loop
        self.simulation_update_accumulator = 0.0
        self.taskMgr.add(self.simulation_update_task, "simulation_update")

        # Tasks
        self.taskMgr.add(self.update_task, "update")
        
        print("✅ Panda3D Simulator initialized")
    
    def setup_lighting(self):
        """Setup 3D lighting."""
        # Ambient light
        ambient_light = AmbientLight("ambient")
        ambient_light.setColor((0.8, 0.8, 0.8, 1.0))
        self.render.attachNewNode(ambient_light).node()
        self.render.setLight(self.render.getChild(self.render.getNumChildren()-1))
        
        # Fog for depth and atmosphere
        scene_fog = Fog("scene_fog")
        scene_fog.setColor(0.75, 0.88, 0.96)
        scene_fog.setExpDensity(0.0012)
        self.render.setFog(scene_fog)
        
        # Directional light (sunset)
        directional_light = DirectionalLight("sun")
        directional_light.setColor((1.0, 0.84, 0.6, 1.0))
        directional_light.setShadowCaster(True, 2048, 2048)
        directional_light.getLens().setFilmSize(50, 50)
        directional_light.getLens().setNearFar(10, 150)
        sun_node = self.render.attachNewNode(directional_light)
        sun_node.setPos(40, 80, 30)
        sun_node.lookAt(0, 0, 0)
        self.render.setLight(sun_node)
        self.render.setShaderAuto()
        
        # Point light
        point_light = PointLight("point")
        point_light.setColor((0.9, 0.9, 1.0, 1.0))
        point_node = self.render.attachNewNode(point_light)
        point_node.setPos(0, 30, 0)
        point_light.setAttenuation((1.0, 0.04, 0.007))
        self.render.setLight(point_node)
    
    def setup_ui(self):
        """Setup UI text."""
        font = self.loader.loadFont("cmss12") or self.loader.loadFont("cmr12.egg")
        self.stats_text = OnscreenText(
            text="",
            pos=(-1.3, 0.9),
            fg=(1, 1, 1, 1),
            align=TextNode.A_left,
            scale=0.05,
            font=font
        )
    
    def set_simulation(self, sim):
        """Connect simulation to renderer."""
        self.simulation = sim
    
    def update_task(self, task):
        """Update simulation each frame."""
        self.frame_count += 1
        if self.simulation is None:
            return Task.cont
        
        # Update organisms
        for organism in self.simulation.organisms:
            org_id = organism.uid
            
            if org_id not in self.organism_models and organism.is_alive:
                # Create new model
                model = OrganismModel3D(
                    self.organisms_node,
                    org_id,
                    organism.x,
                    organism.y
                )
                self.organism_models[org_id] = model
            
            if org_id in self.organism_models:
                model = self.organism_models[org_id]
                
                if organism.is_alive:
                    emotion = "normal"
                    if hasattr(organism, 'get_emotion_state'):
                        emotion = organism.get_emotion_state()
                    
                    model.update(organism.x, organism.y, self.frame_count, emotion)
                else:
                    # Remove dead organism
                    model.remove()
                    del self.organism_models[org_id]
        
        # Update UI
        alive_count = len([o for o in self.simulation.organisms if o.is_alive])
        stats = f"""Digital Organism Simulator - Panda3D
Organisms: {alive_count}/{len(self.simulation.organisms)}
Generation: {self.simulation.evolution_tracker.current_generation}
Births: {self.simulation.evolution_tracker.total_births}
FPS: {globalClock.getAverageFrameRate():.0f}

Controls:
  Mouse: Rotate view
  W/A/S/D: Move camera
  Q/E: Up/Down
  ESC: Quit
"""
        self.stats_text.setText(stats)
        
        return Task.cont
    
    def simulation_update_task(self, task):
        """Advance the simulation on a fixed tick rate while rendering."""
        if self.simulation is None:
            return Task.cont

        dt = globalClock.getDt()
        self.simulation_update_accumulator += dt
        tick_interval = 1.0 / max(1, self.simulation.tick_rate)
        while self.simulation_update_accumulator >= tick_interval:
            self.simulation.update()
            self.simulation_update_accumulator -= tick_interval

        return Task.cont

    def update_camera_task(self, task):
        """Update camera rotation and movement."""
        if self.mouseWatcherNode.hasMouse():
            pointer = self.win.getPointer(0)
            dx = pointer.getX() - self.center_x
            dy = pointer.getY() - self.center_y
            if dx != 0 or dy != 0:
                self.camera_yaw += dx * self.mouse_sensitivity
                self.camera_pitch = max(-80.0, min(80.0, self.camera_pitch - dy * self.mouse_sensitivity))
                self.camera.setHpr(self.camera_yaw, self.camera_pitch, 0)
                self.win.movePointer(0, self.center_x, self.center_y)

        dt = globalClock.getDt()
        move_dir = Vec3(0, 0, 0)
        if self.mouseWatcherNode.is_button_down(KeyboardButton.ascii_key(b'w')):
            move_dir += self.camera.getQuat(self.render).getForward()
        if self.mouseWatcherNode.is_button_down(KeyboardButton.ascii_key(b's')):
            move_dir -= self.camera.getQuat(self.render).getForward()
        if self.mouseWatcherNode.is_button_down(KeyboardButton.ascii_key(b'd')):
            move_dir += self.camera.getQuat(self.render).getRight()
        if self.mouseWatcherNode.is_button_down(KeyboardButton.ascii_key(b'a')):
            move_dir -= self.camera.getQuat(self.render).getRight()
        if move_dir.lengthSquared() > 0:
            move_dir.setZ(0)
            move_dir.normalize()
            new_pos = self.camera.getPos() + move_dir * self.camera_speed * dt
            self.camera.setX(max(-WORLD_WIDTH * 1.2, min(WORLD_WIDTH * 1.2, new_pos.getX())))
            self.camera.setY(max(-WORLD_HEIGHT * 1.2, min(WORLD_HEIGHT * 1.2, new_pos.getY())))
            self.camera.setZ(max(5.0, min(80.0, new_pos.getZ())))

        if self.mouseWatcherNode.is_button_down(KeyboardButton.ascii_key(b'e')):
            self.camera.setZ(max(5.0, min(80.0, self.camera.getZ() + self.camera_speed * dt)))
        if self.mouseWatcherNode.is_button_down(KeyboardButton.ascii_key(b'q')):
            self.camera.setZ(max(5.0, min(80.0, self.camera.getZ() - self.camera_speed * dt)))

        return Task.cont

    def handle_window_event(self, window):
        properties = window.getProperties()
        if not properties.getOpen():
            print("window closed by window manager")

    def handle_input(self):
        """Handle keyboard input."""
        pass


def run_3d_simulator(simulation):
    """Run the Panda3D simulator."""
    simulator = Panda3DSimulator()
    simulator.set_simulation(simulation)
    simulator.run()
