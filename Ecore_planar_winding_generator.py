import FreeCAD as App
import Part
import math

# ==============================================================================
# 1. PARAMETER CONFIGURATION (Inches to mm)
# ==============================================================================
INCH_TO_MM = 25.4

# Core hole sizing
CORE_W = 4.17       # 1.524 mm
CORE_H = 15 + 0.095 * INCH_TO_MM       # 3.048 mm

# Winding rules
TRACE_W = 0.014 * INCH_TO_MM      # 
TRACE_SPACE = 0.008 * INCH_TO_MM  # (10 mils)
NUM_TURNS = 8

# Geometry corners & clearances
R_BASE = 0.020 * INCH_TO_MM       # 20 mils base centerline radius for turn 0
CORE_CLEARANCE = 1.016            # 40 mils mechanical clearance
PITCH = TRACE_W + TRACE_SPACE

# Create a new document in FreeCAD
doc = App.newDocument("PlanarMagneticsWinding")

# ==============================================================================
# 2. GENERATE THE CENTRAL CORE REFERENCE CUTOUT
# ==============================================================================
# Create a rectangular box showing the core cutout hole boundaries
core_rect = Part.makeRectangle(CORE_W, CORE_H)
# Center the rectangle at (0, 0)
core_rect.translate(App.Vector(-CORE_W/2, -CORE_H/2, 0))

core_obj = doc.addObject("Part::Feature", "Core_Cutout_Hole")
core_obj.Shape = core_rect
core_obj.ViewObject.LineColor = (1.0, 0.0, 0.0) # Red reference

# ==============================================================================
# 3. COMPUTE CENTERLINE SPIRAL WIRE
# ==============================================================================
w_start = (CORE_W / 2) + CORE_CLEARANCE + (TRACE_W / 2)
h_start = (CORE_H / 2) + CORE_CLEARANCE + (TRACE_W / 2)

edges = []

# A. Inside Lead-In Tail
inner_lead_x = -w_start + TRACE_W + TRACE_SPACE
p_start = App.Vector(inner_lead_x, -h_start, 0)

# B. Main Spiral Windings (Building sequential straight segments and curved arcs)
p_prev = p_start

for turn in range(NUM_TURNS):
    offset = turn * PITCH
    w_c = w_start + offset
    h_c = h_start + offset
    r_curr = R_BASE + offset
    
    h_next = h_start + ((turn + 1) * PITCH)
    
    # Target quadrant points for the corners
    # 1. Bottom Right Corner
    p_br_in  = App.Vector(w_c - r_curr, -h_c, 0)
    p_br_out = App.Vector(w_c, -h_c + r_curr, 0)
    p_br_mid = App.Vector(w_c - r_curr * (1 - math.cos(math.pi/4)), -h_c + r_curr * (1 - math.sin(math.pi/4)), 0)
    
    # 2. Top Right Corner
    p_tr_in  = App.Vector(w_c, h_c - r_curr, 0)
    p_tr_out = App.Vector(w_c - r_curr, h_c, 0)
    p_tr_mid = App.Vector(w_c - r_curr * (1 - math.cos(math.pi/4)), h_c - r_curr * (1 - math.sin(math.pi/4)), 0)
    
    # 3. Top Left Corner
    p_tl_in  = App.Vector(-w_c + r_curr, h_c, 0)
    p_tl_out = App.Vector(-w_c, h_c - r_curr, 0)
    p_tl_mid = App.Vector(-w_c + r_curr * (1 - math.cos(math.pi/4)), h_c - r_curr * (1 - math.sin(math.pi/4)), 0)
    
    # 4. Left Side Transition Drop
    p_bl_in  = App.Vector(-w_c, -h_next + r_curr, 0)
    p_bl_out = App.Vector(-w_c + r_curr, -h_next, 0)
    p_bl_mid = App.Vector(-w_c + r_curr * (1 - math.cos(math.pi/4)), -h_next + r_curr * (1 - math.sin(math.pi/4)), 0)
    
    # --- STITCH CHANNELS AND ARCS TOGETHER NATIVELY ---
    # Segment 1: Bottom edge line -> Bottom-Right Arc
    edges.append(Part.makeLine(p_prev, p_br_in))
    edges.append(Part.Arc(p_br_in, p_br_mid, p_br_out).toShape())
    
    # Segment 2: Right vertical edge line -> Top-Right Arc
    edges.append(Part.makeLine(p_br_out, p_tr_in))
    edges.append(Part.Arc(p_tr_in, p_tr_mid, p_tr_out).toShape())
    
    # Segment 3: Top horizontal edge line -> Top-Left Arc
    edges.append(Part.makeLine(p_tr_out, p_tl_in))
    edges.append(Part.Arc(p_tl_in, p_tl_mid, p_tl_out).toShape())
    
    # Segment 4: Left vertical edge line -> Bottom-Left Arc
    edges.append(Part.makeLine(p_tl_out, p_bl_in))
    
    if turn < NUM_TURNS - 1:
        # Standard step-down turn to proceed to next loop pass
        edges.append(Part.Arc(p_bl_in, p_bl_mid, p_bl_out).toShape())
        p_prev = p_bl_out
    else:
        # Final pass: Complete the loop's final turn and cap cleanly
        edges.append(Part.Arc(p_bl_in, p_bl_mid, p_bl_out).toShape())
        p_prev = p_bl_out

# Combine independent lines and arc segments into a single 3D Wire object
centerline_wire = Part.Wire(edges)


# Add the final shape to the project document tree
trace_obj = doc.addObject("Part::Feature", "Planar_Copper_Winding")
trace_obj.Shape = ribbon_face
trace_obj.ViewObject.FaceColor = (0.0, 0.8, 0.2) # Green Trace Shape

# Refresh workspace view viewport panels
doc.recompute()
App.Gui.activeDocument().activeView().viewAxonometric()
App.Gui.activeDocument().activeView().fitAll()

print("complete")