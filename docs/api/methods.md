# Hydraulic methods

Lower-level public calculations for applications that need to assemble or inspect a
hydraulic workflow explicitly. All dimensions and hydraulic values use SI units.

::: culvert_solver
    options:
      members:
        - calculate_inlet_control_headwater
        - calculate_modern_box_inlet_headwater
        - unsubmerged_headwater_form_1
        - unsubmerged_headwater_form_2
        - submerged_headwater
        - transition_headwater
        - flow_parameter
        - calculate_full_flow_outlet_headwater
        - calculate_partial_flow_outlet_headwater
        - calculate_downstream_full_flow_length
        - calculate_entrance_loss
        - calculate_friction_loss
        - calculate_exit_loss
        - calculate_total_head_loss
        - compute_backwater_profile
        - compute_inlet_control_s2_profile
        - compute_steep_inlet_control_profile
        - calculate_roadway_overtopping
        - calculate_critical_depth
        - calculate_normal_depth
        - calculate_channel_normal_depth
        - calculate_sequent_depth
        - cross_section_velocity
        - velocity_head
        - specific_energy
        - water_surface_elevation_from_energy_grade
        - froude_number
        - hydraulic_radius
        - manning_discharge
        - manning_friction_slope
        - friction_head_loss
        - minor_head_loss
        - hydrostatic_pressure_moment
        - momentum_function
        - dimension_mm_to_m
        - solve_bracketed
        - solve_brent
        - resolve_inlet_coefficients
        - resolve_modern_box_inlet_coefficients
        - resolve_entrance_loss_coefficient
        - resolve_exit_loss_coefficient
        - resolve_manning_roughness
        - resolve_csp_manning_roughness
      show_root_heading: false
      heading_level: 2
