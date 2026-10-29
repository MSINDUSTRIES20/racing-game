"""
=========================================================================================
HORIZON: ULTRA SIMULATION ENGINE - ENTERPRISE BUILD (v12.0.0 - THE GRAND MASTER BUILD)
=========================================================================================
Architecture & Subsystems: 
- Advanced Procedural Track Generation (Multi-Octave Sine Waves)
- Granular Vehicle Physics (Torque Curves, Gear Ratios, Aerodynamic Drag, Friction)
- Tire Thermodynamics & Chassis Suspension Dynamics (Weight Transfer)
- Dynamic Object Pooling & Memory Management (Garbage Collection optimization)
- Multi-Biome Weather & Particle Engine (VFX)
- Finite State Machine AI Rival Logic
- Multi-Camera Director System & Telemetry Data Mining
- Civilian Traffic AI & Collision Avoidance System
- Advanced Gearbox Tuning System
- Dynamic Time of Day Global Illumination
- Post-Race Telemetry Analytics Graphing Engine
- NEW: AI Driver Personas (Aggressive, Pro, Cautious)
- NEW: Corporate Sponsorship & Contract Engine
- NEW: RGB Custom Paint Shop
- NEW: Procedural Starfield Generation
=========================================================================================
"""

from ursina import *
from ursina.shaders import lit_with_shadows_shader, unlit_shader
import random
import math
import time as pytime

# =======================================================================================
# [1] ENGINE INITIALIZATION & CORE CONFIGURATIONS
# =======================================================================================
app = Ursina()
window.title = "Horizon: Ultra Simulation Engine"
window.fps_counter.enabled = True
window.exit_button.visible = False
window.vsync = False

# Global Lighting Pipeline
sun = DirectionalLight(shadows=True)
sun.look_at(Vec3(1, -1, 1))
sun.shadow_map_resolution = (2048, 2048) # High-res shadows for Intel Arc GPUs
ambient = AmbientLight(color=color.rgba(120, 120, 140, 1))

# =======================================================================================
# [2] PERSISTENT DATA, ECONOMY, TUNING, FLEET & SPONSORS
# =======================================================================================
class PlayerProfile:
    """Manages player progression, economy, persistent upgrade multipliers, and tuning."""
    def __init__(self):
        self.credits = 35000
        self.upgrades = {
            'engine_level': 1,      # Increases max torque and RPM limit
            'tire_level': 1,        # Increases grip coefficient / cornering speed
            'aero_level': 1,        # Decreases drag coefficient (higher top speed)
            'weight_reduction': 1,  # Decreases mass (better acceleration)
            'nitro_efficiency': 1   # Decreases nitro consumption rate
        }
        
        # Advanced Gearbox Tuning
        self.tuning = {
            'gear_1': 3.50,
            'gear_2': 2.26,
            'gear_3': 1.60,
            'gear_4': 1.25,
            'gear_5': 0.95,
            'gear_6': 0.75,
            'final_drive': 3.73,
            'brake_bias': 0.60,     # Front braking force distribution
            'suspension_stiffness': 1.0
        }
        
        self.stats = {
            'races_played': 0,
            'total_distance_m': 0.0,
            'top_speed_reached_ms': 0.0,
            'total_draft_time': 0.0,
            'total_drift_time': 0.0,
            'traffic_collisions': 0
        }
        
        self.settings = {
            'use_mph': True,
            'graphics_shadows': True,
            'base_fov': 80,
            'time_of_day_cycle': True
        }
        
        # Enterprise Damage & Wear Simulation
        self.wear_and_tear = {
            'engine_health': 100.0,
            'tire_tread': 100.0,
            'oil_quality': 100.0
        }
        
        # Fleet Management Database
        self.fleet = {
            'Apex GT': {'top_speed_mult': 1.0, 'handling_mult': 1.0, 'mass_mult': 1.0, 'owned': True},
            'Vortex V8': {'top_speed_mult': 1.15, 'handling_mult': 0.85, 'mass_mult': 1.2, 'owned': False},
            'Nebula Drift': {'top_speed_mult': 0.9, 'handling_mult': 1.3, 'mass_mult': 0.9, 'owned': False},
            'Titan Heavy': {'top_speed_mult': 0.8, 'handling_mult': 0.7, 'mass_mult': 1.8, 'owned': False},
            'Hyperion X': {'top_speed_mult': 1.3, 'handling_mult': 1.2, 'mass_mult': 0.8, 'owned': False}
        }
        self.active_car = 'Apex GT'
        
        # Paint Customizer RGB Array (Default Red)
        self.custom_paint = [211, 47, 47] 
        
        # Sponsorship System
        self.active_sponsor = None
        self.sponsorship_contracts = {
            'Velocity Racing': {'type': 'speed', 'target': 80.0, 'payout_per_sec': 50, 'desc': 'Stay above 180 MPH'},
            'DriftWorks Inc.': {'type': 'drift', 'target': 1.0, 'payout_per_sec': 100, 'desc': 'Hold continuous drifts'},
            'Aero Dynamics': {'type': 'draft', 'target': 1.0, 'payout_per_sec': 75, 'desc': 'Slipstream opponents'}
        }

    def apply_wear(self, dt, rpm, is_sliding):
        """Simulates mechanical degradation over time."""
        if rpm > 8000:
            self.wear_and_tear['engine_health'] -= (dt * 0.05)
            self.wear_and_tear['oil_quality'] -= (dt * 0.1)
        if is_sliding:
            self.wear_and_tear['tire_tread'] -= (dt * 0.2)
            
        # Clamp values
        for k in self.wear_and_tear:
            self.wear_and_tear[k] = max(0.0, self.wear_and_tear[k])

    def get_mass(self):
        """Calculates vehicle mass in kg based on upgrades and active car."""
        base_mass = 1600 * self.fleet[self.active_car]['mass_mult']
        return base_mass - (self.upgrades['weight_reduction'] * 65)

    def get_drag_coef(self):
        """Calculates aerodynamic drag coefficient (Cd)."""
        base_aero = 0.38 / self.fleet[self.active_car]['top_speed_mult']
        return base_aero - (self.upgrades['aero_level'] * 0.025)

    def get_grip(self):
        """Calculates lateral tire grip multiplier including tread wear."""
        tread_modifier = max(0.5, self.wear_and_tear['tire_tread'] / 100.0)
        base_grip = 1.0 * self.fleet[self.active_car]['handling_mult']
        return (base_grip + (self.upgrades['tire_level'] * 0.18)) * tread_modifier

    def get_max_torque(self):
        """Calculates peak engine torque in Nm including engine health."""
        health_mod = max(0.4, self.wear_and_tear['engine_health'] / 100.0)
        base_tq = 450 * self.fleet[self.active_car]['top_speed_mult']
        return (base_tq + (self.upgrades['engine_level'] * 75)) * health_mod

    def get_nitro_drain(self):
        """Calculates how fast nitrous oxide is consumed."""
        return 25.0 - (self.upgrades['nitro_efficiency'] * 2.5)

    def process_sponsor_payouts(self, dt, speed_ms, is_sliding, is_drafting):
        """Evaluates active sponsorship contracts during gameplay and awards micro-credits."""
        if not self.active_sponsor: return 0
        
        contract = self.sponsorship_contracts[self.active_sponsor]
        earned = 0
        
        if contract['type'] == 'speed' and speed_ms >= contract['target']:
            earned = contract['payout_per_sec'] * dt
        elif contract['type'] == 'drift' and is_sliding:
            earned = contract['payout_per_sec'] * dt
        elif contract['type'] == 'draft' and is_drafting:
            earned = contract['payout_per_sec'] * dt
            
        self.credits += earned
        return earned

profile = PlayerProfile()

# =======================================================================================
# [3] ADVANCED PHYSICS SIMULATION CLASSES (Drive-train, Aero, Thermo, Suspension)
# =======================================================================================
class TransmissionSim:
    """Simulates realistic gear shifting, torque multiplication, and RPM mapping."""
    def __init__(self, tuning_ref):
        self.tuning = tuning_ref
        self.update_gears()
        self.current_gear = 0
        self.rpm = 1000
        self.idle_rpm = 1000
        self.redline = 8500
        
    def update_gears(self):
        """Pulls custom gear ratios from player profile tuning."""
        self.gears = [
            self.tuning['gear_1'], self.tuning['gear_2'], self.tuning['gear_3'],
            self.tuning['gear_4'], self.tuning['gear_5'], self.tuning['gear_6']
        ]
        self.final_drive = self.tuning['final_drive']
        
    def calculate_rpm(self, wheel_speed_ms, tire_radius=0.35):
        if self.current_gear >= len(self.gears): 
            return self.redline
            
        # Convert meters/sec to RPM of the wheel, then apply gear ratios
        wheel_rpm = (wheel_speed_ms / (2 * math.pi * tire_radius)) * 60
        new_rpm = wheel_rpm * self.gears[self.current_gear] * self.final_drive
        self.rpm = max(self.idle_rpm, min(self.redline + 500, new_rpm))
        
        # Auto-shift logic with hysteresis to prevent gear-hunting
        if self.rpm > self.redline * 0.94 and self.current_gear < len(self.gears) - 1:
            self.current_gear += 1
        elif self.rpm < self.idle_rpm * 1.6 and self.current_gear > 0:
            self.current_gear -= 1
            
        return self.rpm

class EngineSim:
    """Calculates dynamic torque based on RPM using a simulated dynamometer curve."""
    def __init__(self, profile_ref):
        self.profile = profile_ref
        
    def get_torque(self, rpm, throttle):
        max_tq = self.profile.get_max_torque()
        # Simulated naturally aspirated torque curve peaking at 5800 RPM
        curve_factor = 1.0 - ((abs(rpm - 5800) / 5800) ** 2.2) 
        actual_torque = max_tq * max(0.2, curve_factor) * throttle
        return max(0, actual_torque)

class TireThermodynamics:
    """Simulates tire surface and core temperatures based on friction and load."""
    def __init__(self):
        self.surface_temp = 35.0  # Ambient start (Celsius)
        self.core_temp = 35.0
        self.optimal_temp = 85.0
        self.overheat_temp = 125.0
        
    def update(self, dt, speed_ms, is_sliding, lateral_g):
        # Base heating from rolling resistance
        heating_rate = (speed_ms * 0.05) * dt
        
        # Massive heating from sliding/drifting
        if is_sliding:
            heating_rate += (speed_ms * 0.8) * dt
            
        # Lateral load heating
        heating_rate += (abs(lateral_g) * 5.0) * dt
        
        # Cooling from ambient air
        cooling_rate = ((self.surface_temp - 35.0) * 0.02) * dt
        if speed_ms > 40:
            cooling_rate *= 1.5 # Wind chill at high speeds
            
        self.surface_temp += heating_rate - cooling_rate
        self.surface_temp = max(35.0, min(self.surface_temp, 200.0))
        
        # Core temp slowly follows surface temp
        self.core_temp = lerp(self.core_temp, self.surface_temp, dt * 0.1)
        
    def get_thermal_grip_modifier(self):
        """Returns a grip multiplier based on the bell curve of optimal tire temperatures."""
        if self.core_temp < self.optimal_temp:
            # Cold tires have slightly less grip
            return lerp(0.85, 1.0, (self.core_temp - 35) / (self.optimal_temp - 35))
        elif self.core_temp > self.overheat_temp:
            # Melted/overheated tires lose grip rapidly
            degradation = (self.core_temp - self.overheat_temp) / 50.0
            return max(0.6, 1.0 - degradation)
        else:
            return 1.0

class SuspensionSim:
    """Calculates chassis weight transfer (Pitch and Roll) based on G-Forces and Tuning."""
    def __init__(self, tuning_ref):
        self.tuning = tuning_ref
        self.cg_height = 0.45      # Center of Gravity height in meters
        self.wheelbase = 2.6       # Distance between front and rear axles
        self.track_width = 1.8     # Distance between left and right wheels
        self.pitch_angle = 0.0     # Nose dive / squat
        self.roll_angle = 0.0      # Body roll
        
    def update(self, dt, long_g, lat_g):
        # Calculate ideal angles based on spring stiffness constants and user tuning
        stiffness = self.tuning['suspension_stiffness']
        target_pitch = (long_g * (self.cg_height / self.wheelbase) * -8.0) / stiffness
        target_roll = (lat_g * (self.cg_height / self.track_width) * -12.0) / stiffness
        
        # Apply damping/spring rates using lerp for smooth physics visualization
        self.pitch_angle = lerp(self.pitch_angle, target_pitch, dt * 8.0)
        self.roll_angle = lerp(self.roll_angle, target_roll, dt * 6.0)

# =======================================================================================
# [4] GAME SYSTEMS (ACHIEVEMENTS, CAMERA DIRECTOR, TELEMETRY LOGGING)
# =======================================================================================
class AchievementSystem:
    """Monitors gameplay stats and issues rewards for milestones."""
    def __init__(self):
        self.milestones = {
            'speed_demon': {'target': 89.4, 'reward': 5000, 'desc': "Reach 200 MPH", 'achieved': False},
            'marathon': {'target': 10000, 'reward': 10000, 'desc': "Drive 10,000m total", 'achieved': False},
            'drift_king': {'target': 30, 'reward': 7500, 'desc': "Slide for 30s total", 'achieved': False}
        }
        
    def check_milestones(self, game_ref, profile_ref):
        if not self.milestones['speed_demon']['achieved'] and game_ref.speed_ms >= self.milestones['speed_demon']['target']:
            self.trigger_achievement('speed_demon', profile_ref)
            
        if not self.milestones['marathon']['achieved'] and profile_ref.stats['total_distance_m'] >= self.milestones['marathon']['target']:
            self.trigger_achievement('marathon', profile_ref)
            
        if not self.milestones['drift_king']['achieved'] and profile_ref.stats['total_drift_time'] >= self.milestones['drift_king']['target']:
            self.trigger_achievement('drift_king', profile_ref)
            
    def trigger_achievement(self, key, profile_ref):
        self.milestones[key]['achieved'] = True
        reward = self.milestones[key]['reward']
        profile_ref.credits += reward
        show_notification(f"ACHIEVEMENT UNLOCKED!\n{self.milestones[key]['desc']}\n+ ${reward}")

achievements = AchievementSystem()

class TelemetryLogger:
    """Logs speed and physics data every second for post-race analytics graphing."""
    def __init__(self):
        self.speed_history = []
        self.time_history = []
        self.log_timer = 0.0
        
    def reset(self):
        self.speed_history.clear()
        self.time_history.clear()
        self.log_timer = 0.0
        
    def log_frame(self, dt, speed_ms, lap_time):
        self.log_timer += dt
        if self.log_timer >= 0.5: # Log twice a second
            self.log_timer = 0.0
            self.speed_history.append(speed_ms)
            self.time_history.append(lap_time)

telemetry_db = TelemetryLogger()

class GhostRecorder:
    """Enterprise system to record precise frame-by-frame telemetry for Ghost AI."""
    def __init__(self):
        self.frames = []
        self.is_recording = False
        
    def reset_and_record(self):
        self.frames.clear()
        self.is_recording = True
        
    def capture_frame(self, player_ent, speed, _dt):
        del _dt
        if not self.is_recording: return
        self.frames.append({
            'x': player_ent.x,
            'y': player_ent.y,
            'z': player_ent.z,
            'rot_y': player_ent.rotation_y,
            'rot_z': player_ent.rotation_z,
            'speed': speed
        })
        
    def save_ghost_to_disk(self):
        """Simulated function to compress and export run data."""
        pass # In a full release, this would write a binary file.

ghost_system = GhostRecorder()

class CameraDirector:
    """Handles multiple camera angles and ensures perfect Z-axis (Roll) locking."""
    def __init__(self):
        self.mode = 0 # 0: Chase, 1: Hood, 2: Bumper, 3: Cinematic/Heli
        self.modes_count = 4
        self.shake_intensity = 0.0
        
    def switch_camera(self):
        self.mode = (self.mode + 1) % self.modes_count
        
    def update(self, dt, player_ent, speed_ratio, is_boosting):
        base_fov = profile.settings['base_fov']
        target_fov = base_fov + (speed_ratio * 35)
        if is_boosting: target_fov += 25
        camera.fov = lerp(camera.fov, target_fov, dt * 4)
        
        if speed_ratio > 0.8 or is_boosting:
            self.shake_intensity = (speed_ratio - 0.7) * 0.5 if not is_boosting else 0.8
        else:
            self.shake_intensity = 0.0
            
        shake_vec = Vec3(random.uniform(-self.shake_intensity, self.shake_intensity), 
                         random.uniform(-self.shake_intensity, self.shake_intensity), 0)

        # Mode 0: Standard Chase Cam (Strict Z-Axis Lock to fix sideways glitch)
        if self.mode == 0:
            target_cam = player_ent.position + player_ent.up * (4.5 - speed_ratio) - player_ent.forward * (11 + (speed_ratio*4))
            camera.position = lerp(camera.position, target_cam + shake_vec, dt * 12)
            camera.look_at(player_ent.position + player_ent.forward * 30)
            camera.rotation_z = 0 # CRITICAL: Forces the horizon level, preventing sideways tilting!
            
        # Mode 1: Hood Cam
        elif self.mode == 1:
            target_cam = player_ent.position + player_ent.up * 1.5 + player_ent.forward * 0.5
            camera.position = lerp(camera.position, target_cam + (shake_vec * 0.5), dt * 20)
            camera.rotation_y = player_ent.rotation_y
            camera.rotation_x = player_ent.rotation_x
            camera.rotation_z = player_ent.rotation_z
            
        # Mode 2: Bumper Cam
        elif self.mode == 2:
            target_cam = player_ent.position + player_ent.up * 0.5 + player_ent.forward * 2.8
            camera.position = lerp(camera.position, target_cam + (shake_vec * 0.8), dt * 20)
            camera.rotation_y = player_ent.rotation_y
            camera.rotation_x = player_ent.rotation_x
            camera.rotation_z = player_ent.rotation_z
            
        # Mode 3: Helicopter Cinematic Cam (Strict Z-Axis Lock)
        elif self.mode == 3:
            target_cam = player_ent.position + Vec3(20, 15, -20)
            camera.position = lerp(camera.position, target_cam, dt * 3)
            camera.look_at(player_ent.position + player_ent.forward * 10)
            camera.rotation_z = 0

cam_director = CameraDirector()

# =======================================================================================
# [5] DYNAMIC BIOME & LEVEL MANAGER
# =======================================================================================
class LevelConfig:
    """Configuration class for distinct environmental biomes and weather conditions."""
    def __init__(self, name, sky_col, fog_den, road_col, offroad_col, grip_mod, is_night, has_snow, rain_chance=0.0):
        self.name = name
        self.sky_col = sky_col
        self.fog_den = fog_den
        self.road_col = road_col
        self.offroad_col = offroad_col
        self.grip_mod = grip_mod
        self.is_night = is_night
        self.has_snow = has_snow
        self.rain_chance = rain_chance

# Expanded Enterprise Level Definitions
LEVELS = {
    1: LevelConfig("Autumn Valley", color.hex('#6EB5FF'), 0.003, color.hex('#2A2A2A'), color.hex('#4E7B35'), 1.0, False, False, 0.4),
    2: LevelConfig("Midnight Neon", color.hex('#020205'), 0.008, color.hex('#080808'), color.hex('#030303'), 1.3, True, False, 0.8),
    3: LevelConfig("Winter Tundra", color.hex('#B0C4DE'), 0.018, color.hex('#C0C0C0'), color.hex('#FFFFFF'), 0.45, False, True, 0.0),
    4: LevelConfig("Desert Canyon", color.hex('#FFB070'), 0.004, color.hex('#3A3025'), color.hex('#C28F5B'), 0.9, False, False, 0.0),
    5: LevelConfig("Cyber City",    color.hex('#1A0033'), 0.007, color.hex('#111115'), color.hex('#0A0A0F'), 1.1, True, False, 0.9),
    6: LevelConfig("Tropical Coast", color.hex('#00BFFF'), 0.002, color.hex('#333333'), color.hex('#EEDC82'), 1.05, False, False, 0.6),
    7: LevelConfig("Volcanic Pass", color.hex('#8B0000'), 0.006, color.hex('#1C1C1C'), color.hex('#3E0000'), 0.8, False, False, 0.0)
}

active_level = LEVELS[1]

# =======================================================================================
# [6] PARTICLE & VFX ENGINE (Fixed Memory & Alpha Pipeline)
# =======================================================================================
class ParticleSystem(Entity):
    """High-performance custom particle engine with dynamic memory handling."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.particles = []
        
    def emit(self, position, velocity, p_color, life, size, model='cube'):
        p = Entity(model=model, scale=size, position=position, shader=unlit_shader)
        # Store original color components in the dictionary to avoid Panda3D extraction errors
        self.particles.append({
            'ent': p, 
            'vel': velocity, 
            'life': life, 
            'max_life': life,
            'col_vec': (p_color[0], p_color[1], p_color[2]) # Store raw RGB
        })
        
    def update_particles(self, dt):
        for p in self.particles[:]:
            p['life'] -= dt
            if p['life'] <= 0:
                destroy(p['ent'])
                self.particles.remove(p)
            else:
                p['ent'].position += p['vel'] * dt
                scale_factor = p['life'] / p['max_life']
                p['ent'].scale *= 0.95 # Shrink over time
                
                # FIXED ALPHA PIPELINE: Create a new Vec4 every frame to prevent AttributeError
                r, g, b = p['col_vec']
                p['ent'].color = Vec4(r, g, b, scale_factor)

vfx = ParticleSystem()

# =======================================================================================
# [7] CORE GAME STATE & MATH ARCHITECTURE
# =======================================================================================
class GameState:
    """Master state controller for routing and global variables."""
    def __init__(self):
        self.state = 'menu' # states: menu, garage, tuning, options, sponsors, level_select, playing, game_over, paused
        self.distance = 0
        self.speed_ms = 0
        self.start_time = pytime.time()
        self.lap_time = 0.0
        self.g_force_lateral = 0.0
        self.g_force_longitudinal = 0.0
        
        # New Simulation Variables
        self.nitro_capacity = 100.0
        self.draft_charge = 0.0  
        self.is_boosting = False
        self.is_drafting = False
        self.pause_start_time = 0.0
        self.total_paused_time = 0.0
        self.time_of_day_phase = 0.0 # 0.0 to 1.0 representing full day cycle
        
game = GameState()

# Procedural Track Generation Algorithms (Multi-Octave Sine Waves for unpredictability)
def get_track_pos(z):
    wave1 = math.sin(z / 150.0) * 40
    wave2 = math.sin(z / 400.0) * 50
    wave3 = math.sin(z / 800.0) * 100
    return wave1 + wave2 + wave3

def get_track_rot(z):
    x1 = get_track_pos(z)
    x2 = get_track_pos(z + 1)
    return math.degrees(math.atan2(x2 - x1, 1))

# =======================================================================================
# [8] VEHICLE ARCHITECTURE (PLAYER, AI RACERS, CIVILIAN TRAFFIC)
# =======================================================================================
class Vehicle(Entity):
    """Complex vehicle class handling mesh generation, physics states, and sub-systems."""
    def __init__(self, primary_color, is_player=False):
        super().__init__()
        self.is_player = is_player
        self.lane_offset = 0
        self.steer_angle = 0
        self.velocity = Vec3(0,0,0)
        self.speed_ms = 0
        self.is_sliding = False
        
        # NEW: Advanced AI Personas 
        # Dictates how aggressive or cautious the AI drives
        self.ai_persona = random.choice(['aggressive', 'pro', 'cautious', 'defender'])
        
        # Sub-systems Integration
        self.transmission = TransmissionSim(profile.tuning)
        self.engine = EngineSim(profile)
        self.thermo = TireThermodynamics()
        self.suspension = SuspensionSim(profile.tuning)
        
        # Build Mesh Base Container (Separated for independent suspension roll/pitch)
        self.chassis = Entity(parent=self)
        self.body_color = primary_color
        self._build_mesh()
        
        # Hitbox (BoxCollider)
        self.collider = BoxCollider(self, center=Vec3(0, 0.6, 0), size=Vec3(2.6, 1.2, 5.2))

    def update_paint(self):
        """Allows dynamically applying RGB paint values from the Garage."""
        if self.is_player:
            r, g, b = profile.custom_paint
            self.body_color = color.rgba(r, g, b, 255)
        
        for c in self.chassis.children:
            if hasattr(c, 'is_paintable') and c.is_paintable:
                c.color = self.body_color

    def _build_mesh(self):
        Entity(parent=self.chassis, model='cube', color=color.hex('#111111'), scale=(2.6, 0.2, 5.2), y=0.3, shader=lit_with_shadows_shader)
        
        # Main Body panels marked as paintable
        body1 = Entity(parent=self.chassis, model='cube', color=self.body_color, scale=(2.5, 0.5, 4.8), y=0.55, shader=lit_with_shadows_shader)
        body1.is_paintable = True
        body2 = Entity(parent=self.chassis, model='cube', color=self.body_color, scale=(2.3, 0.3, 2.0), position=(0, 0.5, 1.5), rotation_x=12, shader=lit_with_shadows_shader)
        body2.is_paintable = True
        
        Entity(parent=self.chassis, model='sphere', color=color.hex('#050505'), scale=(1.8, 0.8, 2.6), y=0.8, z=-0.2, shader=lit_with_shadows_shader)
        Entity(parent=self.chassis, model='cube', color=color.hex('#111111'), scale=(0.1, 0.8, 0.4), position=(1.0, 0.9, -2.2), rotation_x=-15, shader=lit_with_shadows_shader)
        Entity(parent=self.chassis, model='cube', color=color.hex('#111111'), scale=(0.1, 0.8, 0.4), position=(-1.0, 0.9, -2.2), rotation_x=-15, shader=lit_with_shadows_shader)
        
        wing = Entity(parent=self.chassis, model='cube', color=self.body_color, scale=(3.4, 0.1, 0.8), position=(0, 1.3, -2.4), shader=lit_with_shadows_shader)
        wing.is_paintable = True
        
        self.hl = Entity(parent=self.chassis, model='cube', color=color.white, scale=(2.0, 0.15, 0.1), position=(0, 0.55, 2.4), shader=unlit_shader)
        self.tl = Entity(parent=self.chassis, model='cube', color=color.red, scale=(2.3, 0.15, 0.1), position=(0, 0.6, -2.4), shader=unlit_shader)

        self.front_wheels, self.rear_wheels = [], []
        for x_pos in [1.35, -1.35]:
            fw = Entity(parent=self, model='sphere', color=color.hex('#1A1A1A'), scale=(0.6, 1.1, 1.1), position=(x_pos, 0.55, 1.5), shader=lit_with_shadows_shader)
            Entity(parent=fw, model='sphere', color=color.hex('#CCCCCC'), scale=(1.05, 0.6, 0.6), x=(0.1 if x_pos>0 else -0.1), shader=lit_with_shadows_shader)
            self.front_wheels.append(fw)
            rw = Entity(parent=self, model='sphere', color=color.hex('#1A1A1A'), scale=(0.7, 1.2, 1.2), position=(x_pos, 0.6, -1.5), shader=lit_with_shadows_shader)
            Entity(parent=rw, model='sphere', color=color.hex('#CCCCCC'), scale=(1.05, 0.6, 0.6), x=(0.1 if x_pos>0 else -0.1), shader=lit_with_shadows_shader)
            self.rear_wheels.append(rw)

class CivilianTraffic(Entity):
    """Slow moving obstacle cars on the highway."""
    def __init__(self, type_id=0):
        super().__init__()
        self.speed_ms = random.uniform(15, 25)
        self.lane_offset = random.choice([-8, -4, 0, 4, 8])
        self.chassis = Entity(parent=self)
        
        if type_id == 0: # Sedan
            c_col = random.choice([color.white, color.gray, color.blue, color.black])
            Entity(parent=self.chassis, model='cube', color=c_col, scale=(2.4, 0.6, 5.0), y=0.5, shader=lit_with_shadows_shader)
            Entity(parent=self.chassis, model='cube', color=color.hex('#222222'), scale=(2.0, 0.6, 2.5), y=1.0, z=-0.5, shader=lit_with_shadows_shader)
            self.collider = BoxCollider(self, center=Vec3(0, 0.5, 0), size=Vec3(2.4, 1.2, 5.0))
        elif type_id == 1: # Delivery Truck
            Entity(parent=self.chassis, model='cube', color=color.white, scale=(2.8, 2.5, 7.0), y=1.5, z=-1.0, shader=lit_with_shadows_shader)
            Entity(parent=self.chassis, model='cube', color=color.red, scale=(2.8, 1.5, 2.0), y=1.0, z=3.0, shader=lit_with_shadows_shader)
            self.collider = BoxCollider(self, center=Vec3(0, 1.5, 0), size=Vec3(2.8, 2.5, 9.0))
            
        self.wheels = []
        for x_pos in [1.3, -1.3]:
            for z_pos in [1.5, -1.5]:
                w = Entity(parent=self, model='sphere', color=color.black, scale=(0.5, 1.0, 1.0), position=(x_pos, 0.5, z_pos), shader=lit_with_shadows_shader)
                self.wheels.append(w)

# =======================================================================================
# [9] PROCEDURAL ARCHITECTURE & DENSE FOLIAGE CLASSES
# =======================================================================================
class ProceduralProp(Entity):
    """Base class for all auto-generated roadside architecture."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.shader = lit_with_shadows_shader

class OakTree(ProceduralProp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Entity(parent=self, model='cube', color=color.hex('#4A3525'), scale=(1.5, 5, 1.5), y=2.5, shader=self.shader)
        leaf_col = random.choice([color.hex('#D2691E'), color.hex('#FF8C00'), color.hex('#DAA520'), color.hex('#2E4A35')])
        Entity(parent=self, model='sphere', color=leaf_col, scale=(6, 7, 6), y=6, shader=self.shader)
        Entity(parent=self, model='sphere', color=leaf_col, scale=(5, 6, 5), y=5, x=2, shader=self.shader)

class PineTree(ProceduralProp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Entity(parent=self, model='cube', color=color.hex('#3E2723'), scale=(1.0, 4, 1.0), y=2, shader=self.shader)
        Entity(parent=self, model='cube', color=color.hex('#1B5E20'), scale=(4, 3, 4), y=4, shader=self.shader)
        Entity(parent=self, model='cube', color=color.hex('#2E7D32'), scale=(3, 3, 3), y=6, shader=self.shader)
        Entity(parent=self, model='cube', color=color.hex('#388E3C'), scale=(1.5, 3, 1.5), y=8, shader=self.shader)

class PalmTree(ProceduralProp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Entity(parent=self, model='cube', color=color.hex('#8B4513'), scale=(0.8, 8, 0.8), y=4, rotation_z=random.uniform(-10, 10), shader=self.shader)
        for _ in range(5):
            Entity(parent=self, model='cube', color=color.hex('#32CD32'), scale=(4, 0.2, 1), y=8, rotation_y=random.uniform(0,360), rotation_x=random.uniform(10,30), shader=self.shader)

class SuburbanHouse(ProceduralProp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        wall_col = random.choice([color.hex('#E0E0E0'), color.hex('#FFE4C4'), color.hex('#D3D3D3')])
        roof_col = random.choice([color.hex('#8B0000'), color.hex('#2F4F4F')])
        Entity(parent=self, model='cube', color=wall_col, scale=(8, 5, 8), y=2.5, shader=self.shader)
        Entity(parent=self, model='cube', color=roof_col, scale=(9, 1.5, 9), y=5.5, rotation_x=10, shader=self.shader)
        Entity(parent=self, model='cube', color=color.hex('#5C4033'), scale=(1.5, 3, 0.2), position=(0, 1.5, -4.1), shader=self.shader)
        Entity(parent=self, model='cube', color=color.black, scale=(2, 1.5, 0.1), position=(2.5, 2.5, -4.1), shader=self.shader)
        Entity(parent=self, model='cube', color=color.black, scale=(2, 1.5, 0.1), position=(-2.5, 2.5, -4.1), shader=self.shader)

class ModernVilla(ProceduralProp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Entity(parent=self, model='cube', color=color.white, scale=(12, 4, 10), y=2.0, shader=self.shader)
        Entity(parent=self, model='cube', color=color.gray, scale=(8, 4, 8), position=(-2, 6.0, 0), shader=self.shader)
        Entity(parent=self, model='cube', color=color.cyan, scale=(5, 3.5, 0.1), position=(2, 2.0, -5.1), shader=unlit_shader)
        Entity(parent=self, model='cube', color=color.cyan, scale=(4, 3.5, 0.1), position=(-2, 6.0, -4.1), shader=unlit_shader)
        Entity(parent=self, model='cube', color=color.black, scale=(9, 0.5, 3), position=(-2, 4.0, -4.5), shader=self.shader)

class CommercialTower(ProceduralProp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        height = random.uniform(30, 70)
        Entity(parent=self, model='cube', color=color.hex('#1A1A1A'), scale=(15, height, 15), y=height/2, shader=self.shader)
        Entity(parent=self, model='cube', color=random.choice([color.cyan, color.magenta, color.orange]), 
               scale=(15.2, 1, 15.2), y=height * 0.8, shader=unlit_shader)
        Entity(parent=self, model='cube', color=random.choice([color.cyan, color.magenta, color.yellow]), 
               scale=(1.0, height * 0.9, 15.2), position=(-7.6, height/2, 0), shader=unlit_shader)

class Bush(ProceduralProp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Entity(parent=self, model='sphere', color=color.hex('#2E4A35'), scale=(3, 2, 3), y=0.5, shader=self.shader)
        Entity(parent=self, model='sphere', color=color.hex('#3B5E2B'), scale=(2.5, 1.8, 2.5), position=(1, 0.4, 0.5), shader=self.shader)
        Entity(parent=self, model='sphere', color=color.hex('#1B5E20'), scale=(2.5, 1.5, 2.5), position=(-1, 0.3, -0.5), shader=self.shader)

class RockCluster(ProceduralProp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        base_col = random.choice([color.hex('#555555'), color.hex('#666666'), color.hex('#444444')])
        if active_level.name == "Volcanic Pass": base_col = color.hex('#111111')
        Entity(parent=self, model='cube', color=base_col, scale=(4, 2, 4), y=0.5, rotation_y=random.uniform(0,360), shader=self.shader)
        Entity(parent=self, model='cube', color=base_col, scale=(3, 3, 3), position=(1.5, 0.8, 1), rotation_z=15, rotation_y=random.uniform(0,360), shader=self.shader)
        Entity(parent=self, model='cube', color=base_col, scale=(2.5, 1.5, 4), position=(-1, 0.2, -1.5), rotation_x=20, shader=self.shader)

class StreetLight(ProceduralProp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Entity(parent=self, model='cube', color=color.dark_gray, scale=(0.4, 15, 0.4), y=7.5, shader=self.shader)
        Entity(parent=self, model='cube', color=color.dark_gray, scale=(6, 0.4, 0.4), position=(2.8, 15, 0), shader=self.shader)
        Entity(parent=self, model='cube', color=color.hex('#FFFFA0'), scale=(2, 0.3, 0.8), position=(4.5, 14.8, 0), shader=unlit_shader)

# =======================================================================================
# [10] DYNAMIC ATMOSPHERICS, WILDLIFE, TIME OF DAY, & STARFIELDS
# =======================================================================================
class ProceduralStarfield:
    """Generates a deep, twinkling starfield visible only during night phases."""
    def __init__(self):
        self.stars = []
        for _ in range(300):
            # Map stars onto a massive dome
            theta = random.uniform(0, 2 * math.pi)
            phi = random.uniform(0, math.pi / 2) # Upper hemisphere only
            radius = random.uniform(2000, 2500)
            
            sx = radius * math.sin(phi) * math.cos(theta)
            sy = radius * math.cos(phi)
            sz = radius * math.sin(phi) * math.sin(theta)
            
            s = Entity(model='sphere', color=color.rgba(255,255,255, random.randint(100,255)), 
                       scale=random.uniform(2, 6), position=(sx, sy, sz), shader=unlit_shader)
            s.base_alpha = s.color.a
            s.twinkle_speed = random.uniform(1, 5)
            s.twinkle_offset = random.uniform(0, 10)
            self.stars.append(s)
            
    def update(self, dt, is_night, player_pos):
        del dt
        for s in self.stars:
            if not is_night:
                s.enabled = False
                continue
                
            s.enabled = True
            # Keep star dome centered on player
            s.position = s.position + (player_pos - s.position) * 0.001 
            # Twinkle math
            twinkle_val = (math.sin(pytime.time() * s.twinkle_speed + s.twinkle_offset) + 1.0) * 0.5
            s.color = color.rgba(255, 255, 255, int(s.base_alpha * twinkle_val))

class VolumetricCloud(Entity):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.drift_speed = random.uniform(2, 6)
        self.drift_dir = Vec3(random.uniform(-1, 1), 0, random.uniform(0.5, 1)).normalized()
        cloud_col = color.rgba(255, 255, 255, random.randint(200, 240))
        num_puffs = random.randint(8, 15)
        for _ in range(num_puffs):
            puff_scale = random.uniform(40, 90)
            puff_pos = Vec3(random.uniform(-40, 40), random.uniform(-10, 10), random.uniform(-40, 40))
            Entity(parent=self, model='sphere', color=cloud_col, scale=puff_scale, position=puff_pos, shader=unlit_shader)
            
    def update_cloud(self, dt):
        self.position += self.drift_dir * self.drift_speed * dt

class AvianEntity(Entity):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.flight_speed = random.uniform(15, 25)
        self.velocity = Vec3(random.uniform(-1, 1), 0, random.uniform(-1, 1)).normalized() * self.flight_speed
        self.flap_speed = random.uniform(15, 25)
        self.flap_time = random.uniform(0, 10)
        self.body = Entity(parent=self, model='cube', color=color.hex('#222222'), scale=(0.5, 0.3, 1.2), shader=lit_with_shadows_shader)
        self.wing_l = Entity(parent=self.body, model='cube', color=color.hex('#333333'), scale=(2.5, 0.1, 0.8), position=(-1.5, 0.1, 0.2), shader=lit_with_shadows_shader)
        self.wing_r = Entity(parent=self.body, model='cube', color=color.hex('#333333'), scale=(2.5, 0.1, 0.8), position=(1.5, 0.1, 0.2), shader=lit_with_shadows_shader)
        self.tail = Entity(parent=self.body, model='cube', color=color.hex('#222222'), scale=(0.8, 0.1, 0.8), position=(0, 0, -0.8), shader=lit_with_shadows_shader)
        
    def update_bird(self, dt, _target_z):
        del _target_z
        self.flap_time += dt * self.flap_speed
        flap_angle = math.sin(self.flap_time) * 35
        self.wing_l.rotation_z = -flap_angle
        self.wing_r.rotation_z = flap_angle
        target_dir = Vec3(math.sin(self.flap_time * 0.1) * 20, math.cos(self.flap_time * 0.2) * 5, 50).normalized()
        self.velocity = lerp(self.velocity, target_dir * self.flight_speed, dt * 1.5)
        self.position += self.velocity * dt
        target_bank = -self.velocity.x * 2.0
        self.rotation_z = lerp(self.rotation_z, target_bank, dt * 4.0)
        self.rotation_y = math.degrees(math.atan2(self.velocity.x, self.velocity.z))

class AmbientNatureSystem:
    def __init__(self):
        self.clouds = []
        self.birds = []
        self.starfield = ProceduralStarfield()
        
    def populate(self):
        self.clear()
        if not active_level.is_night:
            for _ in range(12):
                c_pos = Vec3(random.uniform(-800, 800), random.uniform(300, 600), player.z + random.uniform(200, 3000))
                self.clouds.append(VolumetricCloud(position=c_pos))
        if not active_level.is_night and not active_level.has_snow and active_level.name != "Volcanic Pass":
            for _ in range(20):
                b_pos = Vec3(random.uniform(-150, 150), random.uniform(40, 120), player.z + random.uniform(50, 800))
                self.birds.append(AvianEntity(position=b_pos))
                
    def clear(self):
        for c in self.clouds: destroy(c)
        for b in self.birds: destroy(b)
        self.clouds.clear()
        self.birds.clear()
        
    def tick(self, dt):
        for c in self.clouds:
            c.update_cloud(dt)
            if c.z < player.z - 400:
                c.z = player.z + random.uniform(2500, 3500)
                c.x = player.x + random.uniform(-800, 800)
        for b in self.birds:
            b.update_bird(dt, player.z)
            if b.z < player.z - 100:
                b.z = player.z + random.uniform(600, 1200)
                b.x = player.x + random.uniform(-150, 150)
                b.y = random.uniform(40, 120)
                
        # Determine if it's currently night based on time_of_day phase
        is_night = game.time_of_day_phase > 0.5 and game.time_of_day_phase < 0.9
        if active_level.is_night: is_night = True
        self.starfield.update(dt, is_night, player.position)

class NewsHelicopter(Entity):
    """Cinematic news helicopter that orbits the player during the race."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.body = Entity(parent=self, model='cube', color=color.hex('#1A1A1A'), scale=(2, 2.5, 6), shader=lit_with_shadows_shader)
        self.rotor = Entity(parent=self, model='cube', color=color.black, scale=(12, 0.1, 0.5), y=1.3, shader=lit_with_shadows_shader)
        self.rotor_cross = Entity(parent=self.rotor, model='cube', color=color.black, scale=(0.05, 1, 24), shader=lit_with_shadows_shader)
        self.tail = Entity(parent=self, model='cube', color=color.dark_gray, scale=(0.5, 1, 4), position=(0, 0.5, -4), shader=lit_with_shadows_shader)
        self.orbit_angle = 0.0
        
    def update_heli(self, dt, target_pos):
        self.rotor.rotation_y += dt * 1500
        self.orbit_angle += dt * 0.5
        
        # Smoothly orbit above and ahead of the player
        target_x = target_pos.x + math.sin(self.orbit_angle) * 80
        target_z = target_pos.z + 100 + math.cos(self.orbit_angle) * 80
        target_y = 60 + math.sin(self.orbit_angle * 2) * 10
        
        self.position = lerp(self.position, Vec3(target_x, target_y, target_z), dt * 2)
        self.look_at(target_pos)

nature_sim = AmbientNatureSystem()
heli_cam = NewsHelicopter(enabled=False)

class AdvancedWeatherDirector:
    """Manages dynamic meteorological events like Rain, Thunderstorms, and Road Slickness."""
    def __init__(self):
        self.is_raining = False
        self.rain_intensity = 0.0
        self.lightning_flash = 0.0
        self.storm_timer = 0.0
        
    def evaluate_biome(self, level):
        if random.random() < level.rain_chance:
            self.is_raining = True
            self.rain_intensity = random.uniform(0.5, 1.0)
            self.storm_timer = random.uniform(30, 90)
        else:
            self.is_raining = False
            self.rain_intensity = 0.0
            
    def update(self, dt, player_ent, speed):
        if not self.is_raining: return
        
        self.storm_timer -= dt
        if self.storm_timer <= 0:
            self.is_raining = False
            self.rain_intensity = 0.0
            return
            
        # Spawn massive rain particle system
        for _ in range(int(10 * self.rain_intensity)):
            r_pos = player_ent.position + player_ent.forward * random.uniform(20, 80) + Vec3(random.uniform(-40,40), random.uniform(20, 40), 0)
            r_vel = Vec3(random.uniform(-1, 1), -random.uniform(30, 50), -speed * 0.8)
            vfx.emit(r_pos, r_vel, color.rgba(150, 150, 255, 180), 1.0, 0.1, 'cube')
            
        if self.rain_intensity > 0.8 and random.random() < 0.01:
            self.lightning_flash = 1.0
            
        if self.lightning_flash > 0:
            self.lightning_flash -= dt * 5
            ambient.color = color.rgba(200, 200, 255, max(0.5, self.lightning_flash))
        elif active_level.is_night:
            ambient.color = color.rgba(15, 15, 20, 1)

weather_sim = AdvancedWeatherDirector()

def update_time_of_day(dt):
    """Dynamically shifts lighting colors to simulate a full day-night cycle."""
    if not profile.settings['time_of_day_cycle'] or active_level.is_night: return
    
    game.time_of_day_phase = (game.time_of_day_phase + (dt / 120.0)) % 1.0
    
    dawn_sky = color.hex('#FF9C7A')
    noon_sky = active_level.sky_col
    dusk_sky = color.hex('#FF6347')
    night_sky = color.hex('#020205')
    
    if game.time_of_day_phase < 0.25: # Dawn to Noon
        t = game.time_of_day_phase / 0.25
        cur_sky = color.rgb(
            lerp(dawn_sky.r, noon_sky.r, t),
            lerp(dawn_sky.g, noon_sky.g, t),
            lerp(dawn_sky.b, noon_sky.b, t)
        )
    elif game.time_of_day_phase < 0.5: # Noon to Dusk
        t = (game.time_of_day_phase - 0.25) / 0.25
        cur_sky = color.rgb(
            lerp(noon_sky.r, dusk_sky.r, t),
            lerp(noon_sky.g, dusk_sky.g, t),
            lerp(noon_sky.b, dusk_sky.b, t)
        )
    elif game.time_of_day_phase < 0.75: # Dusk to Night
        t = (game.time_of_day_phase - 0.5) / 0.25
        cur_sky = color.rgb(
            lerp(dusk_sky.r, night_sky.r, t),
            lerp(dusk_sky.g, night_sky.g, t),
            lerp(dusk_sky.b, night_sky.b, t)
        )
    else: # Night to Dawn
        t = (game.time_of_day_phase - 0.75) / 0.25
        cur_sky = color.rgb(
            lerp(night_sky.r, dawn_sky.r, t),
            lerp(night_sky.g, dawn_sky.g, t),
            lerp(night_sky.b, dawn_sky.b, t)
        )
        
    scene.fog_color = cur_sky
    window.color = cur_sky

# =======================================================================================
# [11] WORLD GENERATION & DYNAMIC MEMORY POOLING (Infinite Environment)
# =======================================================================================
# 🚨 BUG FIX: Initialize arrays here safely without 'global' keyword to avoid Python SyntaxErrors
ai_cars = []
traffic_cars = []
track_pieces = []
scenery_pool = []
hills = []

def build_environment():
    for e in track_pieces + scenery_pool + hills + traffic_cars: destroy(e)
    track_pieces.clear()
    scenery_pool.clear()
    hills.clear()
    traffic_cars.clear()
    
    scene.fog_density = active_level.fog_den
    scene.fog_color = active_level.sky_col
    window.color = active_level.sky_col
    game.time_of_day_phase = 0.25 # Start at noon
    
    if active_level.is_night:
        sun.disable() 
        ambient.color = color.rgba(15, 15, 20, 1) 
    else:
        sun.enable()
        sun.color = color.white
        if not profile.settings['graphics_shadows']:
            sun.disable()
        ambient.color = color.rgba(120, 120, 140, 1)

    terrain_shader = unlit_shader if active_level.is_night else lit_with_shadows_shader
    if not profile.settings['graphics_shadows']: terrain_shader = unlit_shader

    nature_sim.populate()

    for _ in range(25):
        z_pos = random.uniform(200, 2500)
        side = random.choice([-1, 1])
        x_pos = get_track_pos(z_pos) + (side * random.uniform(400, 1500))
        h = Entity(model='sphere', color=active_level.offroad_col, scale=(400, 150, 400), y=-40, z=z_pos, x=x_pos, shader=terrain_shader)
        hills.append(h)

    for i in range(80): 
        z = i * 12
        x = get_track_pos(z)
        rot = get_track_rot(z)
        anchor = Entity(position=(x, 0, z), rotation_y=rot)
        
        Entity(parent=anchor, model='cube', color=active_level.road_col, scale=(24, 0.1, 12.1), shader=terrain_shader)
        
        if active_level.is_night:
            Entity(parent=anchor, model='cube', color=color.cyan, scale=(0.5, 0.5, 12.1), position=(-12, 0.25, 0), shader=unlit_shader)
            Entity(parent=anchor, model='cube', color=color.magenta, scale=(0.5, 0.5, 12.1), position=(12, 0.25, 0), shader=unlit_shader)
        else:
            edge_col = color.white if i % 2 == 0 else color.red
            Entity(parent=anchor, model='cube', color=edge_col, scale=(1.0, 0.15, 12.1), position=(-12.5, 0, 0), shader=terrain_shader)
            Entity(parent=anchor, model='cube', color=edge_col, scale=(1.0, 0.15, 12.1), position=(12.5, 0, 0), shader=terrain_shader)
            if i % 2 == 0:
                Entity(parent=anchor, model='cube', color=color.hex('#FFD700'), scale=(0.4, 0.15, 6), position=(0, 0, 0), shader=unlit_shader)
        
        Entity(parent=anchor, model='cube', color=active_level.offroad_col, scale=(200, 0.05, 12.1), x=-112, shader=terrain_shader)
        Entity(parent=anchor, model='cube', color=active_level.offroad_col, scale=(200, 0.05, 12.1), x=112, shader=terrain_shader)
        track_pieces.append(anchor)

        if i % 2 == 0:
            for side in [-1, 1]:
                cluster_density = random.randint(3, 6) 
                for _ in range(cluster_density):
                    x_offset = random.uniform(20, 150) * side 
                    z_offset = z + random.uniform(-10, 10)
                    spawn_pos = (x + x_offset, 0, z_offset)
                    choice = random.random()
                    scenery_ent = None
                    
                    if active_level.name == "Cyber City":
                        if choice < 0.6: scenery_ent = CommercialTower(position=spawn_pos)
                        elif choice < 0.8: scenery_ent = StreetLight(position=spawn_pos)
                    elif active_level.name == "Desert Canyon":
                        if choice < 0.2: scenery_ent = SuburbanHouse(position=spawn_pos)
                        elif choice < 0.5: scenery_ent = RockCluster(position=spawn_pos)
                        elif choice < 0.7: scenery_ent = Bush(position=spawn_pos)
                    elif active_level.name == "Winter Tundra":
                        if choice < 0.5: scenery_ent = PineTree(position=spawn_pos)
                        elif choice < 0.7: scenery_ent = RockCluster(position=spawn_pos)
                        elif choice < 0.8: scenery_ent = SuburbanHouse(position=spawn_pos) 
                    elif active_level.name == "Midnight Neon":
                        if choice < 0.3: scenery_ent = StreetLight(position=spawn_pos)
                        elif choice < 0.6: scenery_ent = CommercialTower(position=spawn_pos)
                    elif active_level.name == "Tropical Coast":
                        if choice < 0.5: scenery_ent = PalmTree(position=spawn_pos)
                        elif choice < 0.7: scenery_ent = Bush(position=spawn_pos)
                        else: scenery_ent = ModernVilla(position=spawn_pos)
                    elif active_level.name == "Volcanic Pass":
                        if choice < 0.8: scenery_ent = RockCluster(position=spawn_pos)
                    else: 
                        if choice < 0.25: scenery_ent = OakTree(position=spawn_pos)
                        elif choice < 0.50: scenery_ent = PineTree(position=spawn_pos)
                        elif choice < 0.65: scenery_ent = Bush(position=spawn_pos)
                        elif choice < 0.75: scenery_ent = RockCluster(position=spawn_pos)
                        elif choice < 0.85: scenery_ent = SuburbanHouse(position=spawn_pos)
                        else: scenery_ent = ModernVilla(position=spawn_pos)
                        
                    if scenery_ent:
                        scenery_ent.rotation_y = random.uniform(0, 360)
                        if not profile.settings['graphics_shadows']:
                            for child in scenery_ent.children: child.shader = unlit_shader
                        scenery_pool.append(scenery_ent)
                        
    # Spawn Initial Traffic
    for t_idx in range(6):
        tc = CivilianTraffic(type_id=random.randint(0,1))
        tc.z = 200 + (t_idx * 150)
        traffic_cars.append(tc)

def recycle_environment():
    if game.state != 'playing': return
    if track_pieces[0].z < player.z - 50:
        p = track_pieces.pop(0)
        new_z = track_pieces[-1].z + 12
        p.z, p.x, p.rotation_y = new_z, get_track_pos(new_z), get_track_rot(new_z)
        track_pieces.append(p)

    for s in scenery_pool:
        if s.z < player.z - 50:
            s.z = player.z + random.uniform(700, 1000)
            side = random.choice([-1, 1])
            s.x = get_track_pos(s.z) + (random.uniform(20, 150) * side)

    for h in hills:
        if h.z < player.z - 300:
            h.z = player.z + random.uniform(1500, 2500)
            h.x = get_track_pos(h.z) + (random.choice([-1, 1]) * random.uniform(400, 1500))
            
    for tc in traffic_cars:
        if tc.z < player.z - 50:
            tc.z = player.z + random.uniform(400, 800)
            tc.lane_offset = random.choice([-8, -4, 0, 4, 8])
            tc.speed_ms = random.uniform(15, 25)

# =======================================================================================
# [12] UI & HUD ARCHITECTURE (Menu Routing, Settings, Graphing)
# =======================================================================================
ui_manager = Entity(parent=camera.ui)

# Notification Popup System
notif_bg = Entity(parent=ui_manager, model='quad', color=color.rgba(30,144,255, 230), scale=(0.8, 0.15), position=(0, 0.6))
notif_text = Text(parent=notif_bg, text="", origin=(0,0), scale=5, color=color.white)
notif_timer = 0

def show_notification(msg):
    global notif_timer
    notif_text.text = msg
    notif_bg.y = 0.4
    notif_timer = 3.0

def update_notifications(dt):
    global notif_timer
    if notif_timer > 0:
        notif_timer -= dt
        if notif_timer <= 0:
            notif_bg.y = 0.8 # Hide off screen

# --- 1. Main Menu ---
menu_screen = Entity(parent=ui_manager)
Entity(parent=menu_screen, model='quad', color=color.rgba(0,0,0,220), scale=(3, 3), z=1)
Text(text="HORIZON: ULTRA SIMULATION", parent=menu_screen, y=0.35, scale=3.5, origin=(0,0), color=color.white)
credits_text = Text(text=f"Credits: ${profile.credits}", parent=menu_screen, position=(-0.85, 0.45), scale=2, color=color.green)

# --- 2. Advanced Telemetry HUD (Fixed positions) ---
telemetry_hud = Entity(parent=ui_manager, enabled=False)
Entity(parent=telemetry_hud, model='quad', color=color.rgba(0,0,0,180), scale=(0.35, 0.7), position=(-0.70, 0))
tel_title = Text(parent=telemetry_hud, text="TELEMETRY (T to hide)", position=(-0.85, 0.32), scale=1.5, color=color.cyan)
tel_speed = Text(parent=telemetry_hud, text="SPD: 0.0 m/s", position=(-0.85, 0.25), scale=1.5)
tel_rpm = Text(parent=telemetry_hud, text="RPM: 1000", position=(-0.85, 0.20), scale=1.5)
tel_gear = Text(parent=telemetry_hud, text="GEAR: N", position=(-0.85, 0.15), scale=1.5)
tel_torque = Text(parent=telemetry_hud, text="TRQ: 0 Nm", position=(-0.85, 0.10), scale=1.5)
tel_drag = Text(parent=telemetry_hud, text="AERO: 0 N", position=(-0.85, 0.05), scale=1.5)
tel_glat = Text(parent=telemetry_hud, text="G-LAT: 0.00 G", position=(-0.85, 0.00), scale=1.5)
tel_glon = Text(parent=telemetry_hud, text="G-LON: 0.00 G", position=(-0.85, -0.05), scale=1.5)
tel_tire = Text(parent=telemetry_hud, text="TIRE TEMP: 35C", position=(-0.85, -0.10), scale=1.5, color=color.orange)
tel_pitch = Text(parent=telemetry_hud, text="PITCH: 0.0", position=(-0.85, -0.15), scale=1.5, color=color.yellow)
tel_roll = Text(parent=telemetry_hud, text="ROLL: 0.0", position=(-0.85, -0.20), scale=1.5, color=color.yellow)
tel_biome = Text(parent=telemetry_hud, text="BIOME: None", position=(-0.85, -0.30), scale=1.5, color=color.hex('#00FF00'))

# --- 3. Arcade HUD (Forza Style) ---
arcade_hud = Entity(parent=ui_manager, enabled=False)
ui_speed_num = Text(parent=arcade_hud, position=(0.65, -0.35), text="0", scale=5, color=color.white)
ui_speed_unit = Text(parent=arcade_hud, position=(0.78, -0.40), text="MPH", scale=2, color=color.hex('#AAAAAA'))

# PERFECTLY SPACED UI TO PREVENT OVERLAPS (FIXED Y-COORDINATES)
time_bg = Entity(parent=arcade_hud, model='quad', color=color.rgba(0,0,0,180), scale=(0.5, 0.22), position=(0, -0.38))
Text(parent=time_bg, origin=(0,0), position=(0, 0.20), text="Lap Time", scale=5.5, color=color.hex('#AAAAAA'))
ui_time = Text(parent=time_bg, origin=(0,0), position=(0, -0.25), text="00:00.000", scale=10, color=color.white)

leader_bg = Entity(parent=arcade_hud, model='quad', color=color.rgba(0,0,0,180), scale=(0.4, 0.38), position=(0.70, 0.28))
Entity(parent=leader_bg, model='quad', color=color.hex('#CCFF00'), scale=(1, 0.12), position=(0, 0.44))
Text(parent=leader_bg, origin=(0,0), position=(0, 0.44), text="Live Position", scale=6, color=color.black)
leaderboard_ui = [Text(parent=leader_bg, position=(-0.45, 0.25 - (i*0.18)), text=f"{i+1}. ", scale=6, color=color.white) for i in range(5)]

nitro_bg = Entity(parent=arcade_hud, model='quad', color=color.rgba(30,30,30,200), scale=(0.4, 0.03), position=(0, -0.24))
nitro_bar = Entity(parent=nitro_bg, model='quad', color=color.cyan, scale=(0.98, 0.8), position=(0, 0, -0.1))
Text(text="N2O", parent=nitro_bg, scale=12, position=(-0.48, 0), origin=(-0.5, 0), color=color.white)

draft_bg = Entity(parent=arcade_hud, model='quad', color=color.rgba(30,30,30,200), scale=(0.4, 0.03), position=(0, -0.28))
draft_bar = Entity(parent=draft_bg, model='quad', color=color.orange, scale=(0.001, 0.8), position=(0, 0, -0.1))
Text(text="DRAFT", parent=draft_bg, scale=12, position=(-0.48, 0), origin=(-0.5, 0), color=color.white)
draft_indicator = Text(parent=arcade_hud, text="SLIPSTREAM ACTIVE", position=(0, -0.20), origin=(0,0), scale=2, color=color.clear)

# NEW: Simulated Radio UI
radio_bg = Entity(parent=arcade_hud, model='quad', color=color.rgba(10,10,10, 180), scale=(0.3, 0.06), position=(-0.7, 0.45))
Text(parent=radio_bg, text="RADIO | FM", position=(-0.45, 0.2), scale=3, color=color.hex('#AAAAAA'))
radio_track = Text(parent=radio_bg, text="TRACK: Synthwave_01", position=(-0.45, -0.3), scale=4, color=color.white)

# NEW: Minimap Radar System
minimap_bg = Entity(parent=arcade_hud, model='sphere', color=color.rgba(0,0,0, 150), scale=(0.25, 0.25), position=(-0.7, -0.3))
Entity(parent=minimap_bg, model='sphere', color=color.rgba(255,255,255, 50), scale=(1.05, 1.05), z=0.1) # Border
map_player_dot = Entity(parent=minimap_bg, model='sphere', color=color.green, scale=(0.1, 0.1), position=(0, -0.05, -0.2))
map_ai_dots = [Entity(parent=minimap_bg, model='sphere', color=color.red, scale=(0.08, 0.08), z=-0.2) for _ in range(4)]

def update_minimap():
    """Calculates relative distance to render dots on the circular HUD map."""
    scale_factor = 0.0015 # Map scale ratio
    for i, ai in enumerate(ai_cars):
        z_diff = (ai.z - player.z) * scale_factor
        x_diff = (ai.lane_offset - player.lane_offset) * 0.02
        # Clamp to circle
        if z_diff > 0.4: z_diff = 0.4
        if z_diff < -0.4: z_diff = -0.4
        map_ai_dots[i].position = (x_diff, -0.05 + z_diff)

# --- 3.5 Pause Menu (Escape Screen) ---
pause_screen = Entity(parent=ui_manager, enabled=False)
Entity(parent=pause_screen, model='quad', color=color.rgba(0,0,0,230), scale=(3, 3), z=1)
Text(text="PAUSED", parent=pause_screen, y=0.25, scale=5, origin=(0,0), color=color.white)

def toggle_pause():
    """Toggles pause state and safely disables HUD elements to prevent visual overlapping."""
    if game.state == 'playing':
        game.state = 'paused'
        game.pause_start_time = pytime.time()
        
        pause_screen.enabled = True
        arcade_hud.enabled = False
        telemetry_hud.enabled = False
        
    elif game.state == 'paused':
        game.state = 'playing'
        game.total_paused_time += (pytime.time() - game.pause_start_time)
        
        pause_screen.enabled = False
        arcade_hud.enabled = True
        telemetry_hud.enabled = show_telemetry

Button(text='RESUME', parent=pause_screen, y=0.05, scale=(0.4, 0.08), color=color.hex('#4CAF50'), on_click=toggle_pause)
Button(text='QUIT TO MENU', parent=pause_screen, y=-0.08, scale=(0.4, 0.08), color=color.hex('#D32F2F'), on_click=lambda: route_to_menu())
Button(text='QUIT TO DESKTOP', parent=pause_screen, y=-0.21, scale=(0.4, 0.08), color=color.hex('#8B0000'), on_click=application.quit)

# Universal Input Handler
def input(key):
    if key == 'escape':
        if game.state in ['playing', 'paused']:
            toggle_pause()
    if key == 'c' and game.state == 'playing':
        cam_director.switch_camera()

# --- 4. Game Over & Analytics Screen ---
go_screen = Entity(parent=ui_manager, enabled=False)
Entity(parent=go_screen, model='quad', color=color.rgba(10, 10, 10, 240), scale=(3, 3), z=1)
Text(text="RACE FINISHED", parent=go_screen, y=0.35, scale=5, origin=(0,0), color=color.white)
go_stats = Text(text="", parent=go_screen, y=0.15, scale=2, origin=(0,0), color=color.hex('#AAAAAA'))
graph_container = Entity(parent=go_screen, y=-0.15)
graph_bars = []

def generate_telemetry_graph():
    """Generates a bar/line graph of the speed history from the race."""
    for b in graph_bars: destroy(b)
    graph_bars.clear()
    
    if len(telemetry_db.speed_history) < 2: return
    
    # Background for graph
    b = Entity(parent=graph_container, model='quad', color=color.rgba(255,255,255, 30), scale=(1.2, 0.4), z=-0.1)
    graph_bars.append(b)
    t = Text(parent=graph_container, text="Telemetry: Speed Profile", position=(-0.6, 0.22), scale=2)
    graph_bars.append(t)
    
    max_spd = max(telemetry_db.speed_history)
    if max_spd == 0: max_spd = 1
    
    num_points = len(telemetry_db.speed_history)
    width_per_point = 1.2 / num_points
    
    for i, spd in enumerate(telemetry_db.speed_history):
        normalized_height = (spd / max_spd) * 0.4
        x_pos = -0.6 + (i * width_per_point)
        bar = Entity(parent=graph_container, model='quad', color=color.cyan, 
                     scale=(width_per_point * 0.8, normalized_height), 
                     position=(x_pos, -0.2 + (normalized_height/2)))
        graph_bars.append(bar)

# =======================================================================================
# [13] MENU ROUTING LOGIC, TUNING, SPONSORSHIPS, & PAINT SHOP
# =======================================================================================
def route_to_level_select():
    menu_screen.enabled = False
    level_screen.enabled = True

def route_to_garage():
    menu_screen.enabled = False
    garage_screen.enabled = True
    update_garage_ui()
    
def route_to_tuning():
    menu_screen.enabled = False
    tuning_screen.enabled = True
    
def route_to_options():
    menu_screen.enabled = False
    options_screen.enabled = True
    
def route_to_sponsors():
    menu_screen.enabled = False
    sponsor_screen.enabled = True

def route_to_menu():
    menu_screen.enabled = True
    level_screen.enabled = False
    garage_screen.enabled = False
    tuning_screen.enabled = False
    options_screen.enabled = False
    sponsor_screen.enabled = False
    go_screen.enabled = False
    arcade_hud.enabled = False
    telemetry_hud.enabled = False
    pause_screen.enabled = False
    game.state = 'menu'
    credits_text.text = f"Credits: ${profile.credits}"

# --- Main Menu Buttons ---
Button(text='RACE / SELECT BIOME', parent=menu_screen, y=0.18, scale=(0.4, 0.08), color=color.hex('#D32F2F'), on_click=route_to_level_select)
Button(text='GARAGE & PAINT', parent=menu_screen, y=0.05, scale=(0.4, 0.08), color=color.hex('#1976D2'), on_click=route_to_garage)
Button(text='ADVANCED TUNING', parent=menu_screen, y=-0.08, scale=(0.4, 0.08), color=color.hex('#E65100'), on_click=route_to_tuning)
Button(text='SPONSORSHIPS', parent=menu_screen, y=-0.21, scale=(0.4, 0.08), color=color.hex('#4CAF50'), on_click=route_to_sponsors)
Button(text='OPTIONS / SETTINGS', parent=menu_screen, y=-0.34, scale=(0.4, 0.08), color=color.hex('#555555'), on_click=route_to_options)

# --- Options Screen ---
options_screen = Entity(parent=ui_manager, enabled=False)
Entity(parent=options_screen, model='quad', color=color.rgba(0,0,0,220), scale=(3, 3), z=1)
Text(text="OPTIONS & SETTINGS", parent=options_screen, y=0.3, scale=3.5, origin=(0,0))

def toggle_mph():
    profile.settings['use_mph'] = not profile.settings['use_mph']
    btn_mph.text = 'SPEED: MPH' if profile.settings['use_mph'] else 'SPEED: KM/H'
    ui_speed_unit.text = 'MPH' if profile.settings['use_mph'] else 'KM/H'
    
def toggle_shadows():
    profile.settings['graphics_shadows'] = not profile.settings['graphics_shadows']
    btn_shd.text = 'SHADOWS: ON' if profile.settings['graphics_shadows'] else 'SHADOWS: OFF'
    
def toggle_tod():
    profile.settings['time_of_day_cycle'] = not profile.settings['time_of_day_cycle']
    btn_tod.text = 'DAY CYCLE: ON' if profile.settings['time_of_day_cycle'] else 'DAY CYCLE: OFF'

btn_mph = Button(text='SPEED: MPH', parent=options_screen, y=0.1, scale=(0.4, 0.08), color=color.gray, on_click=toggle_mph)
btn_shd = Button(text='SHADOWS: ON', parent=options_screen, y=-0.02, scale=(0.4, 0.08), color=color.gray, on_click=toggle_shadows)
btn_tod = Button(text='DAY CYCLE: ON', parent=options_screen, y=-0.14, scale=(0.4, 0.08), color=color.gray, on_click=toggle_tod)
Button(text='BACK', parent=options_screen, y=-0.30, scale=(0.2, 0.05), color=color.red, on_click=route_to_menu)

# --- Sponsorship Screen ---
sponsor_screen = Entity(parent=ui_manager, enabled=False)
Entity(parent=sponsor_screen, model='quad', color=color.rgba(0,0,0,220), scale=(3, 3), z=1)
Text(text="CORPORATE SPONSORS", parent=sponsor_screen, y=0.35, scale=3.5, origin=(0,0))
s_active_text = Text(text="Active Sponsor: None", parent=sponsor_screen, y=0.25, scale=2, origin=(0,0), color=color.green)

def sign_sponsor(name):
    profile.active_sponsor = name
    s_active_text.text = f"Active Sponsor: {name}"
    show_notification(f"Signed with {name}!")

y_sp = 0.1
for s_name, data in profile.sponsorship_contracts.items():
    desc = f"{s_name}\nTarget: {data['desc']}\nPayout: ${data['payout_per_sec']}/sec"
    Text(parent=sponsor_screen, text=desc, position=(-0.4, y_sp + 0.03), scale=1.5)
    Button(parent=sponsor_screen, text="SIGN", position=(0.3, y_sp), scale=(0.2, 0.08), color=color.hex('#4CAF50'), on_click=Func(sign_sponsor, s_name))
    y_sp -= 0.15
Button(text='BACK', parent=sponsor_screen, y=-0.4, scale=(0.2, 0.05), color=color.gray, on_click=route_to_menu)

# --- Advanced Tuning Screen ---
tuning_screen = Entity(parent=ui_manager, enabled=False)
Entity(parent=tuning_screen, model='quad', color=color.rgba(0,0,0,220), scale=(3, 3), z=1)
Text(text="GEARBOX & SUSPENSION TUNING", parent=tuning_screen, y=0.35, scale=3.5, origin=(0,0))
Text(text="Warning: Altering gear ratios physically changes acceleration curves!", parent=tuning_screen, y=0.28, scale=1.5, origin=(0,0), color=color.yellow)

def adjust_tune(key, amount):
    profile.tuning[key] = max(0.1, round(profile.tuning[key] + amount, 2))
    render_tuning_ui()

t_texts = []
def render_tuning_ui():
    for t in t_texts: destroy(t)
    t_texts.clear()
    
    y_offsets = [0.15, 0.05, -0.05, -0.15, -0.25, -0.35]
    keys = ['gear_1', 'gear_2', 'gear_3', 'gear_4', 'gear_5', 'gear_6']
    
    for i in range(6):
        k = keys[i]
        val = profile.tuning[k]
        t = Text(parent=tuning_screen, text=f"Gear {i+1} Ratio: {val:.2f}", position=(-0.4, y_offsets[i]), scale=2)
        
        b_down = Button(parent=tuning_screen, text='[-]', position=(0.1, y_offsets[i]+0.02), scale=(0.08, 0.05), color=color.red, on_click=Func(adjust_tune, k, -0.05))
        b_up = Button(parent=tuning_screen, text='[+]', position=(0.2, y_offsets[i]+0.02), scale=(0.08, 0.05), color=color.green, on_click=Func(adjust_tune, k, 0.05))
        t_texts.extend([t, b_down, b_up])
        
Button(text='BACK', parent=tuning_screen, y=-0.42, x=-0.3, scale=(0.2, 0.05), color=color.gray, on_click=route_to_menu)

# --- Level Select Screen ---
level_screen = Entity(parent=ui_manager, enabled=False)
Entity(parent=level_screen, model='quad', color=color.rgba(0,0,0,220), scale=(3, 3), z=1)
Text(text="SELECT BIOME", parent=level_screen, y=0.35, scale=3.5, origin=(0,0))
Button(text='AUTUMN VALLEY', parent=level_screen, y=0.18, scale=(0.4, 0.06), color=color.hex('#D2691E'), on_click=lambda: start_game(1))
Button(text='MIDNIGHT NEON', parent=level_screen, y=0.08, scale=(0.4, 0.06), color=color.hex('#8A2BE2'), on_click=lambda: start_game(2))
Button(text='WINTER TUNDRA', parent=level_screen, y=-0.02, scale=(0.4, 0.06), color=color.hex('#4682B4'), on_click=lambda: start_game(3))
Button(text='DESERT CANYON', parent=level_screen, y=-0.12, scale=(0.4, 0.06), color=color.hex('#CD853F'), on_click=lambda: start_game(4))
Button(text='TROPICAL COAST', parent=level_screen, y=-0.22, scale=(0.4, 0.06), color=color.hex('#2E8B57'), on_click=lambda: start_game(6))
Button(text='VOLCANIC PASS', parent=level_screen, y=-0.32, scale=(0.4, 0.06), color=color.hex('#8B0000'), on_click=lambda: start_game(7))
Button(text='BACK', parent=level_screen, y=-0.42, scale=(0.2, 0.05), color=color.gray, on_click=route_to_menu)

# --- Garage & Paint Shop Screen ---
garage_screen = Entity(parent=ui_manager, enabled=False)
Entity(parent=garage_screen, model='quad', color=color.rgba(0,0,0,220), scale=(3, 3), z=1)
Text(text="UPGRADE & CUSTOMIZE", parent=garage_screen, y=0.35, scale=3.5, origin=(0,0))
garage_creds = Text(text="", parent=garage_screen, position=(-0.85, 0.45), scale=2, color=color.green)

# Paint Shop Logic
Text(text="CUSTOM PAINT (R, G, B)", parent=garage_screen, position=(0.3, 0.25), scale=1.5)
def change_paint(c_idx, val):
    profile.custom_paint[c_idx] = clamp(profile.custom_paint[c_idx] + val, 0, 255)
    player.update_paint()
    render_paint_ui()

p_texts = []
def render_paint_ui():
    for t in p_texts: destroy(t)
    p_texts.clear()
    colors = ['Red', 'Green', 'Blue']
    y_sp = 0.15
    for i in range(3):
        val = profile.custom_paint[i]
        t = Text(parent=garage_screen, text=f"{colors[i]}: {val}", position=(0.3, y_sp), scale=1.5)
        bd = Button(parent=garage_screen, text='[-]', position=(0.25, y_sp+0.01), scale=(0.04, 0.04), color=color.gray, on_click=Func(change_paint, i, -15))
        bu = Button(parent=garage_screen, text='[+]', position=(0.45, y_sp+0.01), scale=(0.04, 0.04), color=color.gray, on_click=Func(change_paint, i, 15))
        p_texts.extend([t, bd, bu])
        y_sp -= 0.08

def buy_upgrade(upgrade_type, cost):
    if profile.credits >= cost and profile.upgrades[upgrade_type] < 5:
        profile.credits -= cost
        profile.upgrades[upgrade_type] += 1
        update_garage_ui()

g_texts = []
def update_garage_ui():
    garage_creds.text = f"Credits: ${profile.credits}"
    for t in g_texts: destroy(t)
    g_texts.clear()
    
    y_offsets = [0.2, 0.1, 0.0, -0.1, -0.2]
    keys = ['engine_level', 'tire_level', 'aero_level', 'weight_reduction', 'nitro_efficiency']
    names = ['Engine (Torque)', 'Tires (Grip)', 'Aero (Drag)', 'Chassis (Weight)', 'Nitro (Capacity)']
    
    for i in range(5):
        lvl = profile.upgrades[keys[i]]
        cost = lvl * 1500
        t = Text(parent=garage_screen, text=f"{names[i]} - Lvl {lvl}", position=(-0.4, y_offsets[i]), scale=1.5)
        g_texts.append(t)
        if lvl < 5:
            btn_color = color.green if profile.credits >= cost else color.gray
            b = Button(parent=garage_screen, text=f'UPGRADE (${cost})', position=(-0.1, y_offsets[i]+0.01), scale=(0.2, 0.05), color=btn_color, on_click=Func(buy_upgrade, keys[i], cost))
            g_texts.append(b)
        else:
            t_max = Text(parent=garage_screen, text="MAXED", position=(-0.1, y_offsets[i]), scale=1.5, color=color.yellow)
            g_texts.append(t_max)
            
    render_paint_ui()

Button(text='BACK', parent=garage_screen, y=-0.42, scale=(0.2, 0.05), color=color.gray, on_click=route_to_menu)
update_garage_ui()
render_tuning_ui()

Button(text='COLLECT REWARD & GRAPH', parent=go_screen, y=-0.4, scale=(0.4, 0.1), color=color.hex('#4CAF50'), on_click=route_to_menu)

# =======================================================================================
# [13.5] ENTERPRISE SUBSYSTEMS (SHOWROOM, MISSIONS, GHOSTS, SKIDMARKS)
# =======================================================================================
class ProceduralSkidMarkEngine:
    def __init__(self, pool_size=400):
        self.pool_size = pool_size
        self.marks = []
        self.current_idx = 0
        for _ in range(self.pool_size):
            mark = Entity(model='quad', color=color.rgba(15, 15, 15, 230), scale=(0.5, 1.2), rotation_x=90, enabled=False)
            self.marks.append(mark)
            
    def place_mark(self, position, rotation_y, intensity=255):
        mark = self.marks[self.current_idx]
        mark.position = position + Vec3(0, 0.03, 0)
        mark.rotation_y = rotation_y
        mark.color = color.rgba(10, 10, 10, int(intensity))
        mark.enabled = True
        self.current_idx = (self.current_idx + 1) % self.pool_size
        
    def reset_track(self):
        for m in self.marks: m.enabled = False

class MissionDirector:
    def __init__(self, profile_ref):
        self.profile = profile_ref
        self.active_mission = None
        self.progress = 0.0
        self.target = 0.0
        self.bg = Entity(parent=camera.ui, model='quad', color=color.rgba(20, 20, 20, 200), scale=(0.4, 0.1), position=(0, 0.42), enabled=False)
        self.title = Text(parent=self.bg, text="ACTIVE BOUNTY", position=(-0.45, 0.3), scale=3, color=color.yellow)
        self.desc = Text(parent=self.bg, text="", position=(-0.45, -0.1), scale=4, color=color.white)
        self.prog_text = Text(parent=self.bg, text="0%", position=(0.3, -0.1), scale=4, color=color.cyan)
        
    def generate_mission(self):
        missions = [
            {'type': 'drift', 'target': 3.0, 'desc': 'Drift for 3 Seconds', 'reward': 1500},
            {'type': 'speed', 'target': 80.0, 'desc': 'Reach 180 MPH', 'reward': 2000},
            {'type': 'draft', 'target': 5.0, 'desc': 'Slipstream for 5s', 'reward': 1200}
        ]
        self.active_mission = random.choice(missions)
        self.progress = 0.0
        self.target = self.active_mission['target']
        self.desc.text = self.active_mission['desc']
        self.prog_text.text = "0%"
        self.bg.enabled = True
        
    def check_progress(self, dt, speed_ms, is_sliding, is_drafting):
        if not self.active_mission: return
        m_type = self.active_mission['type']
        if m_type == 'drift' and is_sliding: self.progress += dt
        elif m_type == 'speed' and speed_ms >= self.target: self.progress = self.target
        elif m_type == 'draft' and is_drafting: self.progress += dt
            
        pct = min(100, int((self.progress / self.target) * 100))
        self.prog_text.text = f"{pct}%"
        if self.progress >= self.target:
            reward = self.active_mission['reward']
            self.profile.credits += reward
            show_notification(f"BOUNTY COMPLETED!\n+ ${reward}")
            self.active_mission = None
            self.bg.enabled = False

class ShowroomTurntable:
    def __init__(self):
        self.container = Entity(enabled=True)
        self.floor = Entity(parent=self.container, model='cylinder', color=color.hex('#111111'), scale=(15, 0.5, 15), y=-0.25, shader=lit_with_shadows_shader)
        self.ring = Entity(parent=self.container, model='torus', color=color.cyan, scale=(8, 0.5, 8), y=0.01, shader=unlit_shader)
        
    def update(self, dt):
        if game.state in ['menu', 'garage', 'tuning', 'options']:
            self.container.enabled = True
            self.floor.rotation_y += dt * 15
        else:
            self.container.enabled = False

class HolographicGhost:
    def __init__(self):
        self.chassis = Entity(model='cube', color=color.rgba(0, 255, 255, 100), scale=(2.5, 0.5, 4.8), shader=unlit_shader, enabled=False)
        self.canopy = Entity(parent=self.chassis, model='sphere', color=color.rgba(0, 200, 255, 150), scale=(0.7, 1.5, 0.5), y=1.0, z=-0.05)
        self.current_frame = 0
        
    def reset(self):
        self.current_frame = 0
        self.chassis.enabled = False
        
    def update_playback(self, frames):
        if not frames or self.current_frame >= len(frames) - 1:
            self.chassis.enabled = False
            return
        self.chassis.enabled = True
        f1 = frames[self.current_frame]
        self.chassis.position = Vec3(f1['x'], f1['y'], f1['z'])
        self.chassis.rotation_y = f1['rot_y']
        self.chassis.rotation_z = f1['rot_z']
        self.current_frame += 1

# =======================================================================================
# [14] GAME LOGIC / INITIALIZATION 
# =======================================================================================

# Initialization of global entity arrays
ai_cars.clear()
traffic_cars.clear()

# Initialize Missing Subsystems (Explicitly scoped globally to prevent NameErrors)
global skid_engine, mission_director, showroom, ghost_visual
skid_engine = ProceduralSkidMarkEngine(pool_size=400)
mission_director = MissionDirector(profile)
showroom = ShowroomTurntable()
ghost_visual = HolographicGhost()

player = Vehicle(color.hex('#D32F2F'), is_player=True)
player.update_paint() # Apply default RGB from profile

for i in range(4):
    ai = Vehicle(random.choice([color.hex('#FBC02D'), color.hex('#1976D2'), color.hex('#F5F5F5'), color.hex('#7B1FA2')]))
    ai_cars.append(ai)

def start_game(level_id):
    """Initializes a race in the selected biome, resets all variables."""
    global active_level
    active_level = LEVELS[level_id]
    tel_biome.text = f"BIOME: {active_level.name}"
    
    build_environment()
    telemetry_db.reset()
    ghost_system.reset_and_record()
    ghost_visual.reset()
    weather_sim.evaluate_biome(active_level)
    skid_engine.reset_track()
    mission_director.generate_mission()
    
    game.speed_ms = 0
    game.distance = 0
    game.start_time = pytime.time()
    game.total_paused_time = 0.0
    game.nitro_capacity = 100.0
    
    # Reload tuning and paint
    player.transmission.update_gears()
    player.update_paint()
    
    # Reset Player
    player.position = (get_track_pos(0), 0, 0)
    player.rotation_y = get_track_rot(0)
    player.lane_offset = 0 
    player.steer_angle = 0
    player.transmission.current_gear = 1
    
    # Reset Physics Visuals
    player.suspension.pitch_angle = 0
    player.suspension.roll_angle = 0
    player.thermo.surface_temp = 35.0
    
    # Reset AI Rivals & Re-roll Personas
    for i, ai in enumerate(ai_cars):
        ai.ai_persona = random.choice(['aggressive', 'pro', 'cautious'])
        ai.z = 100 + (i * 80)
        ai.lane_offset = random.choice([-6, -2, 2, 6])
        ai.speed_ms = 20 
        
    cam_director.mode = 0 # Force default chase cam on start
    camera.rotation_z = 0
    camera.rotation_x = 0
    
    heli_cam.enabled = True
    heli_cam.position = player.position + Vec3(0, 100, 50)
    
    level_screen.enabled = False
    arcade_hud.enabled = True
    telemetry_hud.enabled = True
    mission_director.bg.enabled = True
    game.state = 'playing'

def end_game(reason):
    """Handles the Game Over state, calculates rewards, and draws the analytics graph."""
    game.state = 'game_over'
    arcade_hud.enabled = False
    telemetry_hud.enabled = False
    mission_director.bg.enabled = False
    heli_cam.enabled = False
    go_screen.enabled = True
    
    reward = int(game.distance * 0.1)
    if reason == "finished": reward *= 2
    profile.credits += reward
    
    profile.stats['races_played'] += 1
    ghost_system.save_ghost_to_disk()
    
    go_stats.text = f"Result: {reason.upper()}\nDistance: {int(game.distance)}m\nTime: {ui_time.text}\n\nReward: ${reward}"
    camera.position += (0, 15, -25)
    camera.look_at(player)
    
    generate_telemetry_graph()

# =======================================================================================
# [15] MAIN UPDATE LOOP (Advanced Integration of all Subsystems)
# =======================================================================================
show_telemetry = True

def update():
    """Runs 60+ times per second. Handles Physics, Rendering, AI, and Input."""
    global show_telemetry
    
    dt = time.dt
    
    # SAFEGUARD: Ensure showroom exists before calling update
    if 'showroom' in globals() and showroom is not None:
        showroom.update(dt) # Update 3D menu environment
    
    if held_keys['t']: 
        show_telemetry = not show_telemetry
        telemetry_hud.enabled = show_telemetry
        held_keys['t'] = 0 # Debounce
        
    # Idle Camera Pan for Menus
    if game.state != 'playing': 
        if game.state == 'menu' or game.state == 'garage' or game.state == 'tuning' or game.state == 'options':
            # Orbit Camera around the Showroom Turntable
            orbit_time = pytime.time() * 0.5
            camera.position = (math.sin(orbit_time) * 20, 8, math.cos(orbit_time) * -20)
            camera.look_at((0, 2, 0))
            camera.rotation_z = 0 # Safety lock
        return # PAUSE FREEZES PHYSICS HERE

    vfx.update_particles(dt)
    nature_sim.tick(dt)
    weather_sim.update(dt, player, game.speed_ms)
    update_time_of_day(dt)
    update_notifications(dt)
    
    if heli_cam.enabled:
        heli_cam.update_heli(dt, player.position)
    
    # Log Telemetry & Process Contracts
    telemetry_db.log_frame(dt, game.speed_ms, game.lap_time)
    ghost_system.capture_frame(player, game.speed_ms, dt)
    profile.process_sponsor_payouts(dt, game.speed_ms, player.is_sliding, game.is_drafting)
    
    if len(ghost_system.frames) > 0:
        ghost_visual.update_playback(ghost_system.frames)
    
    update_minimap()
    
    # --- Weather Subsystems ---
    if active_level.has_snow:
        spawn_pos = player.position + player.forward * 60 + Vec3(random.uniform(-50,50), 35, random.uniform(-40,40))
        vfx.emit(spawn_pos, Vec3(0, -18, -game.speed_ms * 1.2), color.white, 2.5, 0.25, 'sphere')
        
    if active_level.name == "Autumn Valley" and game.speed_ms > 10:
        if random.random() < 0.3:
            spawn_pos = player.position + player.forward * random.uniform(30, 80) + Vec3(random.uniform(-20,20), random.uniform(10, 25), 0)
            leaf_col = random.choice([color.hex('#D2691E'), color.hex('#FF8C00'), color.hex('#DAA520')])
            vfx.emit(spawn_pos, Vec3(random.uniform(-2,2), -random.uniform(2,5), -game.speed_ms * 0.2), leaf_col, 3.0, 0.2, 'cube')

    if active_level.name == "Desert Canyon" and game.speed_ms > 10:
        if random.random() < 0.5:
            spawn_pos = player.position + player.forward * random.uniform(20, 60) + Vec3(random.uniform(-15,15), random.uniform(1, 5), 0)
            vfx.emit(spawn_pos, Vec3(random.uniform(-5,5), random.uniform(0,2), -game.speed_ms * 0.5), color.hex('#D2B48C'), 1.5, 0.15, 'sphere')

    # --- Player Input & Drivetrain ---
    throttle, brake, steering_input = 0.0, 0.0, 0.0
    
    if held_keys['w'] or held_keys['up arrow']: throttle = 1.0
    if held_keys['s'] or held_keys['down arrow']: brake = 1.0
    if held_keys['a'] or held_keys['left arrow']: steering_input = -1.0
    if held_keys['d'] or held_keys['right arrow']: steering_input = 1.0

    rpm = player.transmission.calculate_rpm(game.speed_ms)
    torque = player.engine.get_torque(rpm, throttle)
    
    if held_keys['space'] and game.nitro_capacity > 0:
        game.is_boosting = True
        game.nitro_capacity -= dt * profile.get_nitro_drain()
        torque *= 2.5 
        vfx.emit(player.position + player.forward*-2.6 + player.right*-0.5 + player.up*0.6, 
                 Vec3(random.uniform(-1,1), random.uniform(-1,1), -game.speed_ms*2), color.cyan, 0.15, 0.4, 'sphere')
        vfx.emit(player.position + player.forward*-2.6 + player.right*0.5 + player.up*0.6, 
                 Vec3(random.uniform(-1,1), random.uniform(-1,1), -game.speed_ms*2), color.cyan, 0.15, 0.4, 'sphere')
    else:
        game.is_boosting = False
        if game.nitro_capacity < 100.0:
            game.nitro_capacity += dt * 3.5 
            
    nitro_bar.scale_x = max(0.001, (game.nitro_capacity / 100.0) * 0.98)
    nitro_bar.x = -0.49 + (nitro_bar.scale_x / 2) 
    nitro_bar.color = color.cyan if game.nitro_capacity > 20 else color.red

    draft_multiplier = 1.0
    game.is_drafting = False
    for ai in ai_cars:
        dist_to_ai = ai.z - player.z
        if 5.0 < dist_to_ai < 45.0 and abs(ai.lane_offset - player.lane_offset) < 2.5:
            game.is_drafting = True
            draft_multiplier = 0.60 
            if game.speed_ms > 30:
                vfx.emit(player.position + Vec3(random.uniform(-2,2), random.uniform(0.5, 2.0), 3), 
                         Vec3(0, 0, game.speed_ms * 0.8), color.white, 0.2, 0.1)
            break
            
    if game.is_drafting and game.speed_ms > 40:
        draft_indicator.color = color.rgba(255, 255, 255, 255) 
        game.draft_charge = min(100.0, game.draft_charge + (dt * 20)) 
        profile.stats['total_draft_time'] += dt
    else:
        draft_indicator.color = color.rgba(255, 255, 255, max(0, draft_indicator.color.a - (dt*5))) 
        game.draft_charge = max(0.0, game.draft_charge - (dt * 10)) 
        
    draft_bar.scale_x = max(0.001, (game.draft_charge / 100.0) * 0.98)
    draft_bar.x = -0.49 + (draft_bar.scale_x / 2)
    draft_bar.color = color.orange if game.draft_charge < 95 else color.hex('#FF4500')
    
    if game.draft_charge > 95:
        torque *= 1.35 

    air_density = 1.225
    frontal_area = 2.2
    aero_drag = 0.5 * air_density * (game.speed_ms**2) * (profile.get_drag_coef() * draft_multiplier) * frontal_area
    
    rolling_res = 15.0 * profile.get_mass() * 9.81 * 0.015 
    brake_force = brake * 15000
    
    net_force = (torque * player.transmission.gears[player.transmission.current_gear] * 12) - aero_drag - rolling_res - brake_force
    acceleration = net_force / profile.get_mass()
    
    old_speed = game.speed_ms
    game.speed_ms += acceleration * dt
    if game.speed_ms < 0: game.speed_ms = 0
    
    if game.speed_ms > profile.stats['top_speed_reached_ms']:
        profile.stats['top_speed_reached_ms'] = game.speed_ms
    
    game.g_force_longitudinal = ((game.speed_ms - old_speed) / dt) / 9.81
    
    # --- Lateral Dynamics & Steering ---
    max_steer_rate = 3.0
    player.steer_angle = lerp(player.steer_angle, steering_input * 15, dt * max_steer_rate)
    
    player.is_sliding = False
    
    thermal_grip = player.thermo.get_thermal_grip_modifier()
    grip_limit = 11.0 * active_level.grip_mod * profile.get_grip() * thermal_grip
    
    turn_radius = max(0.1, abs(game.speed_ms) / (math.tan(math.radians(max(0.1, abs(player.steer_angle))))))
    centrifugal_accel = (game.speed_ms**2) / turn_radius if steering_input != 0 else 0
    
    actual_turn = player.steer_angle
    if centrifugal_accel > grip_limit:
        actual_turn *= (grip_limit / centrifugal_accel) 
        player.is_sliding = True
        profile.stats['total_drift_time'] += dt
        
        if game.speed_ms > 20:
            if active_level.road_col != color.white:
                vfx.emit(player.position + Vec3(0,0.1,-2), Vec3(random.uniform(-3,3), 2, -game.speed_ms*0.5), color.orange, 0.4, 0.15)
            skid_engine.place_mark(player.position + Vec3(-1.3, 0, -2), player.rotation_y)
            skid_engine.place_mark(player.position + Vec3(1.3, 0, -2), player.rotation_y)

    game.g_force_lateral = (centrifugal_accel / 9.81) * (1 if steering_input > 0 else -1)
    
    player.thermo.update(dt, game.speed_ms, player.is_sliding, game.g_force_lateral)
    player.suspension.update(dt, game.g_force_longitudinal, game.g_force_lateral)
    profile.apply_wear(dt, rpm, player.is_sliding)
    
    # Transform Updates
    player.lane_offset += (actual_turn * game.speed_ms * dt * 0.04)
    player.lane_offset = clamp(player.lane_offset, -11, 11)
    
    player.z += game.speed_ms * dt
    track_x = get_track_pos(player.z)
    track_rot = get_track_rot(player.z)
    
    player.x = track_x + player.lane_offset
    player.rotation_y = track_rot + actual_turn
    
    player.chassis.rotation_x = player.suspension.pitch_angle
    player.chassis.rotation_z = player.suspension.roll_angle
    
    wheel_spin = game.speed_ms * dt * 25
    for w in player.front_wheels:
        w.rotation_x += wheel_spin
        w.rotation_y = player.steer_angle 
    for w in player.rear_wheels:
        w.rotation_x += wheel_spin

    # --- ADVANCED AI PERSONA LOGIC ---
    for i, ai in enumerate(ai_cars):
        ai.z += ai.speed_ms * dt
        ai_track_x = get_track_pos(ai.z)
        
        # Apply persona traits
        if ai.ai_persona == 'aggressive':
            # Weaves wildly, takes blocking lines
            if random.random() < 0.02: ai.lane_offset = lerp(ai.lane_offset, player.lane_offset, dt * 10)
            target_ai_speed = min(95, game.speed_ms * random.uniform(0.98, 1.15))
        elif ai.ai_persona == 'pro':
            # Takes the perfect center racing line
            ai.lane_offset = lerp(ai.lane_offset, 0, dt * 2)
            target_ai_speed = min(90, game.speed_ms * random.uniform(0.95, 1.1))
        else: # Cautious
            # Brakes early, stays out of the way
            if abs(ai.lane_offset - player.lane_offset) < 2.0: ai.lane_offset += (5 * dt)
            target_ai_speed = min(75, game.speed_ms * random.uniform(0.85, 1.0))
            
        ai.x = lerp(ai.x, ai_track_x + ai.lane_offset, dt * 3.5)
        ai.rotation_y = get_track_rot(ai.z)
        for w in ai.front_wheels + ai.rear_wheels: w.rotation_x += ai.speed_ms * dt * 25
        
        dist_to_player = ai.z - player.z
        if dist_to_player < -60: 
            ai.z = player.z + random.uniform(250, 450)
            ai.lane_offset = random.choice([-8, -4, 4, 8])
            ai.speed_ms = game.speed_ms * 0.85
        elif dist_to_player > 600: 
            ai.speed_ms = 25 
        else: 
            ai.speed_ms = lerp(ai.speed_ms, target_ai_speed, dt * 0.6)

    # --- Civilian Traffic AI ---
    for tc in traffic_cars:
        tc.z += tc.speed_ms * dt
        tc.x = get_track_pos(tc.z) + tc.lane_offset
        tc.rotation_y = get_track_rot(tc.z)
        for w in tc.wheels: w.rotation_x += tc.speed_ms * dt * 25
        
        dist = distance(player, tc)
        if dist < 4.5:
            game.speed_ms *= 0.4 
            vfx.emit(player.position + Vec3(0,1,2), Vec3(random.uniform(-5,5), random.uniform(2,8), 5), color.white, 0.8, 0.5, 'sphere')
            profile.stats['traffic_collisions'] += 1
            tc.z += 10 

    # --- Cinematic Camera Director ---
    spd_ratio = game.speed_ms / 110.0
    cam_director.update(dt, player, spd_ratio, game.is_boosting)

    # --- UI Rendering ---
    game.lap_time = pytime.time() - game.start_time - game.total_paused_time
    ui_time.text = f"{int(game.lap_time // 60):02d}:{game.lap_time % 60:06.3f}"
    
    display_spd = game.speed_ms * 2.237 if profile.settings['use_mph'] else game.speed_ms * 3.6
    ui_speed_num.text = str(int(display_spd))
    
    if show_telemetry:
        tel_speed.text = f"SPD: {game.speed_ms:.1f} m/s"
        tel_rpm.text = f"RPM: {int(rpm)}"
        tel_gear.text = f"GEAR: {player.transmission.current_gear+1}"
        tel_torque.text = f"TRQ: {int(torque)} Nm"
        tel_drag.text = f"AERO: {int(aero_drag)} N"
        tel_glat.text = f"G-LAT: {game.g_force_lateral:.2f} G"
        tel_glon.text = f"G-LON: {game.g_force_longitudinal:.2f} G"
        tel_tire.text = f"TIRE TEMP: {int(player.thermo.surface_temp)}C"
        tel_pitch.text = f"PITCH: {player.suspension.pitch_angle:.2f}"
        tel_roll.text = f"ROLL: {player.suspension.roll_angle:.2f}"

    racers = [{'name': 'YOU', 'z': player.z, 'col': color.hex('#CCFF00')}]
    for i, ai in enumerate(ai_cars): 
        # Add persona tag to leaderboard
        tag = ""
        if ai.ai_persona == 'aggressive': tag = " [AGR]"
        elif ai.ai_persona == 'pro': tag = " [PRO]"
        
        racers.append({'name': f'Rival {i+1}{tag}', 'z': ai.z, 'col': color.white})
        
    racers.sort(key=lambda r: r['z'], reverse=True)
    
    for i in range(5):
        leaderboard_ui[i].text = f"{i+1}. {racers[i]['name']}"
        leaderboard_ui[i].color = racers[i]['col']

    # --- GC & Event Triggers ---
    recycle_environment()
    game.distance = player.z
    profile.stats['total_distance_m'] += game.speed_ms * dt
    
    mission_director.check_progress(dt, game.speed_ms, player.is_sliding, game.is_drafting)
    achievements.check_milestones(game, profile)
    
    if player.intersects().hit or abs(player.lane_offset) >= 11.5:
        end_game("wrecked")

app.run()
