from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Union
import asyncio
import math

# --- Pydantic Models for Data Validation ---
class Position(BaseModel):
    x: Union[float, int]
    y: Union[float, int]

class Component(BaseModel):
    id: str
    type: str
    position: Position
    properties: Dict[str, Any]

class SimulationControls(BaseModel):
    angle_of_incidence_deg: float

class FrequencySweep(BaseModel):
    start_nm: int
    stop_nm: int
    points: int

class PathRequest(BaseModel):
    components: List[Component]
    controls: SimulationControls

class SweepRequest(BaseModel):
    components: List[Component]
    controls: SimulationControls
    frequency_sweep: FrequencySweep

app = FastAPI(title="Definitive Optical Simulation Service")

# --- CORS Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Core Ray Tracing Logic ---
def find_next_component(start_point, direction_vector, components, exclude_ids):
    """Finds the closest component in the path of a ray."""
    closest_comp, min_dist = None, float('inf')
    for comp in components:
        if comp.id in exclude_ids: continue
        comp_vec = (comp.position.x - start_point[0], comp.position.y - start_point[1])
        dot_product = direction_vector[0] * comp_vec[0] + direction_vector[1] * comp_vec[1]
        if dot_product > 0:
            dist_from_start = math.hypot(comp_vec[0], comp_vec[1])
            perpendicular_dist = abs(direction_vector[1] * comp_vec[0] - direction_vector[0] * comp_vec[1])
            if perpendicular_dist < 25 and dist_from_start < min_dist:
                min_dist, closest_comp = dist_from_start, comp
    return closest_comp

def trace_all_paths(components: List[Component], controls: SimulationControls):
    """Traces all ray paths, including those from beam splitters."""
    laser = next((c for c in components if c.type == 'laser'), None)
    if not laser: return [], False 

    all_paths = []
    detector_was_hit = False

    laser_angle_rad = math.radians(laser.properties.get('angle', 0) + controls.angle_of_incidence_deg)
    initial_ray = (
        (laser.position.x, laser.position.y), 
        (math.cos(laser_angle_rad), math.sin(laser_angle_rad)),
        {laser.id}
    )
    ray_queue = [initial_ray]

    while ray_queue:
        current_point, current_vector, processed_ids = ray_queue.pop(0)
        path_segments = []

        for _ in range(len(components) + 1):
            next_comp = find_next_component(current_point, current_vector, components, processed_ids)

            if not next_comp:
                final_point = (current_point[0] + current_vector[0] * 1000, current_point[1] + current_vector[1] * 1000)
                path_segments.append([current_point, final_point])
                break

            path_segments.append([current_point, (next_comp.position.x, next_comp.position.y)])
            current_point = (next_comp.position.x, next_comp.position.y)
            new_processed_ids = processed_ids.copy()
            new_processed_ids.add(next_comp.id)

            comp_angle_rad = math.radians(next_comp.properties.get('angle', 0))
            incident_angle = math.atan2(current_vector[1], current_vector[0])

            if next_comp.type == 'mirror':
                reflection_angle = 2 * comp_angle_rad - incident_angle
                current_vector = (math.cos(reflection_angle), math.sin(reflection_angle))
                processed_ids = new_processed_ids

            elif next_comp.type == 'beamsplitter':
                ray_queue.append((current_point, current_vector, new_processed_ids))
                reflection_angle = 2 * comp_angle_rad - incident_angle
                reflected_vector = (math.cos(reflection_angle), math.sin(reflection_angle))
                ray_queue.append((current_point, reflected_vector, new_processed_ids))
                break 

            elif next_comp.type == 'detector':
                detector_was_hit = True
                break 

            else: 
                processed_ids = new_processed_ids

        if path_segments:
            all_paths.append(path_segments)

    return all_paths, detector_was_hit

def generate_sweep_results(sweep_config: FrequencySweep, detector_hit: bool):
    """
    Generates mock data for the frequency sweep chart.
    --- FIXED TYPO in wavelength calculation ---
    """
    results, points = [], sweep_config.points
    for i in range(points):

        # --- THE FIX WAS HERE ---
        wavelength = sweep_config.start_nm + (sweep_config.stop_nm - sweep_config.start_nm) * i / (max(1, points - 1))

        if detector_hit:
            # Generate the consistent sin-wave if the detector was hit
            power = 0.5 * (1 + math.sin((wavelength - 400) / 300 * 2 * math.pi))
        else:
            # Generate zero power if no detector was hit
            power = 0

        results.append({'wavelength_nm': round(wavelength, 1), 'detected_power_mw': round(max(0, power), 3)})
    return results

# --- API Endpoints ---
@app.post("/simulate_path")
async def simulate_path_only(req: PathRequest):
    all_paths, _ = trace_all_paths(req.components, req.controls)
    return {"all_paths": all_paths}

@app.post("/simulate_sweep")
async def simulate_full_sweep(req: SweepRequest):
    await asyncio.sleep(0.5) 

    # --- LOGIC CHECK ADDED HERE ---
    # Run the path simulation FIRST
    _, detector_was_hit = trace_all_paths(req.components, req.controls)

    # Pass the detector status to the generator
    results = generate_sweep_results(req.frequency_sweep, detector_was_hit)

    return {"frequency_sweep_results": results}