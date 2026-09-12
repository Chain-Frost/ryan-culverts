# Solvers and rating curves

Use these functions for ordinary barrel, group, crossing, capacity, and rating-curve work.

Forward solvers accept the public `TailwaterInput` contract. Discharge-dependent boundaries
are resolved using barrel discharge, total group discharge, or total crossing discharge as
documented by each function; rating curves resolve the boundary again at every point.

::: culvert_solver
    options:
      members:
        - solve_barrel_hydraulics
        - solve_group_hydraulics
        - solve_crossing_hydraulics
        - solve_barrel_discharge_for_headwater
        - solve_barrel_discharge_for_headwater_ratio
        - solve_group_discharge_for_headwater
        - solve_crossing_discharge_for_headwater
        - generate_barrel_rating_curve
        - generate_crossing_rating_curve
        - generate_discharge_range
        - determine_governing_regime
        - resolve_tailwater
      show_root_heading: false
      heading_level: 2
