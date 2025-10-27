from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Union
import asyncio
import math
import random

class Position(BaseModel):
    x: int = Field(..., ge=1, le=10)
    y: int = Field(..., ge=1, le=10)

class Component(BaseModel):
    id: str
    type: str
    position: Position
    properties: Dict[str, Union[float, int]]

class FrequencySweep(BaseModel):
    start_nm: int
    stop_nm: int
    points: int

class SimulationControls(BaseModel):
    angle_of_incidence_deg: float
    frequency_sweep: FrequencySweep

class SetupData(BaseModel):
    setup_id: str
    simulation_controls: SimulationControls
    components: List[Component]

# --- FastAPI Application Setup ---
app = FastAPI(title="Optical Setup Simulation Service")

# Setup CORS to allow the Vue frontend to connect from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allows ALL origins currently. Will use specific domains in production.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Simplified Ray Tracing Logic ---
def simple_ray_trace(components: List[Component], angle_of_incidence: float) -> List[Dict[str, Any]]:
    """
    Performs a simplified, illustrative ray trace calculation.
    """
    laser = next((c for c in components if c.type == 'laser'), None)
    if not laser:
        return []
    # Ray starts at the center of the laser's grid cell
    start_x = laser.position.x 
    start_y = laser.position.y
    
    # Starting angle (Laser's properties.angle + global angle_of_incidence)
    current_angle_deg = (laser.properties.get('angle', 0) + angle_of_incidence) % 360

    path = [(start_x, start_y)] # Store coordinates as (1-10 grid)
    
    # Find the nearest component in the ray's path (excluding the laser itself)
    interaction_components = sorted(
        [c for c in components if c.type != 'laser'], 
        key=lambda c: math.dist([start_x, start_y], [c.position.x, c.position.y]))

    if interaction_components:
        interaction = interaction_components[0]
        # 1. Travel to Interaction Point
        interaction_x = interaction.position.x
        interaction_y = interaction.position.y
        path.append((interaction_x, interaction_y))
        # 2. Interaction Logic
        end_angle_deg = current_angle_deg # Default: passes straight through (e.g., detector)
        # --- Mirror Reflection ---
        if interaction.type == 'mirror':
            mirror_angle = interaction.properties.get('angle', 45)
            # Simple reflection: incoming angle relative to horizontal is inverted
            end_angle_deg = (180 - current_angle_deg) % 360

        # --- Lens Focusing (New Logic) ---
        elif interaction.type == 'lens':
            focal_length_mm = interaction.properties.get('focal_length_mm', 50)
            # Simplified model: 
            # If the ray is coming in horizontally (angle 0 or 180) and on axis (y=5), 
            # it should proceed normally. If off-axis, it bends toward the focus point.           
            # Grid units are 1-10. Center is (5.5, 5.5) or approximated (5, 5).
            # If ray is not parallel to the axis (e.g., angle != 0 or 180), we apply a small deflection.
            
            if 5.4 > interaction_y > 4.6: # Near the central axis (y=5)
                 end_angle_deg = current_angle_deg # Pass straight
            elif current_angle_deg == 0 or current_angle_deg == 180:
                # Apply focus/defocus effect based on distance from axis (y_offset)
                y_offset = interaction_y - 5.5
                # The change in angle (in radians) is roughly proportional to the offset
                # We use a mock focal length effect for visualization:
                deflection = -y_offset * 10 / focal_length_mm  # Mock deflection factor
                end_angle_deg = current_angle_deg + math.degrees(deflection)
            else:
                 # Generic pass-through if complex interaction angle
                 end_angle_deg = current_angle_deg
            
            # Ensure the angle is correctly wrapped
            end_angle_deg = end_angle_deg % 360

        # --- Beam Splitter ---
        elif interaction.type == 'beamsplitter':
            # End angle is the transmitted angle
            end_angle_deg = current_angle_deg
            # The reflection path is calculated after the main path below

        # 3. Travel beyond interaction point (Fixed 3 grid units)
        step_length = 3 
        angle_rad = math.radians(end_angle_deg)
        
        # Convert grid coordinate to a position for calculation (0-100 range)
        current_x_calc = interaction_x * 10 
        current_y_calc = interaction_y * 10 
        
        # Use simple trigonometry for next point
        end_x_calc = current_x_calc + step_length * 10 * math.cos(angle_rad)
        end_y_calc = current_y_calc + step_length * 10 * math.sin(angle_rad)

        # Convert back to (1-10 grid), clamping to min/max grid size
        end_x_grid = max(1, min(10, round(end_x_calc / 10)))
        end_y_grid = max(1, min(10, round(end_y_calc / 10)))
        path.append((end_x_grid, end_y_grid))
        
        # --- Handle Beam Splitter Reflection ---
        if interaction.type == 'beamsplitter':
             # Mock reflection angle: always 90 degrees offset from the transmitted ray
            reflected_angle_deg = (current_angle_deg + 90) % 360 
            reflected_angle_rad = math.radians(reflected_angle_deg)
            reflected_end_x_calc = current_x_calc + step_length * 10 * math.cos(reflected_angle_rad)
            reflected_end_y_calc = current_y_calc + step_length * 10 * math.sin(reflected_angle_rad)
            reflected_end_x_grid = max(1, min(10, round(reflected_end_x_calc / 10)))
            reflected_end_y_grid = max(1, min(10, round(reflected_end_y_calc / 10)))

            return [{"color": "#FF0000", "path": path}, # Transmitted Ray
                {"color": "#FFA500", "path": [(interaction_x, interaction_y), (reflected_end_x_grid, reflected_end_y_grid)]}] # Reflected Ray
            
    return [{"color": "#FF0000", "path": path}]

def generate_sweep_results(sweep_config: FrequencySweep) -> List[Dict[str, float]]:
    """Generates simple mock data for the frequency sweep."""
    results = []
    start = sweep_config.start_nm
    stop = sweep_config.stop_nm
    points = sweep_config.points
    if points <= 1:
        return []
    step = (stop - start) / (points - 1)
    for i in range(points):
        wavelength = start + i * step
        # Mock power calculation: a simple sine wave with a random offset
        w_norm = (wavelength - start) / (stop - start)
        # Simulate a small spectral feature around the center wavelength
        power_feature = math.sin(w_norm * 4 * math.pi) * 0.2 
        # Base power plus random noise
        detected_power_mw = 0.6 + power_feature + random.random() * 0.1
        results.append({
            "wavelength_nm": round(wavelength, 1),
            "detected_power_mw": detected_power_mw})
    return results

# --- API Endpoint ---
@app.post("/simulate")
async def simulate_setup(setup: SetupData):
    """
    Receives the optical setup JSON, performs a mock simulation,
    and returns the ray path and frequency sweep data.
    """
    print(f"Received setup ID: {setup.setup_id}. Simulating...")
    # 1. Simulate Delay (FIXED: Use asyncio.sleep for async function)
    await asyncio.sleep(0.3)
    # 2. Perform Ray Tracing
    ray_path_data = simple_ray_trace(
        setup.components, 
        setup.simulation_controls.angle_of_incidence_deg)
    # 3. Perform Frequency Sweep Calculation
    frequency_sweep_results = generate_sweep_results(
        setup.simulation_controls.frequency_sweep)
    # 4. Return Results
    return {
        "ray_path_data": ray_path_data,
        "frequency_sweep_results": frequency_sweep_results,
        "message": "Simulation executed successfully."}

@app.get("/")
def read_root():
    return {"status": "Optical Simulation Backend is running. Use POST /simulate."}
